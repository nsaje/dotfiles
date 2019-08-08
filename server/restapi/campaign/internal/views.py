import rest_framework.permissions
import rest_framework.serializers
from django.db import transaction
from django.db.models import Prefetch

import core.features.bcm
import core.features.bcm.exceptions
import core.features.goals
import core.models
import dash.campaign_goals
import dash.constants
import prodops.hacks
import restapi.access
import restapi.campaign.v1.views
import utils.exc

from . import helpers
from . import serializers


class CampaignViewSet(restapi.campaign.v1.views.CampaignViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.CampaignSerializer

    def validate(self, request):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def defaults(self, request):
        account_id = request.query_params.get("accountId", None)
        if not account_id:
            raise rest_framework.serializers.ValidationError("Must pass accountId parameter")
        account = restapi.access.get_account(request.user, account_id)
        campaign = core.models.Campaign.objects.get_default(request, account)
        self._augment_campaign(request, campaign)
        extra_data = helpers.get_extra_data(request.user, campaign)
        return self.response_ok(
            data=self.serializer(campaign.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id, select_related=True)
        self._augment_campaign(request, campaign)
        extra_data = helpers.get_extra_data(request.user, campaign)
        return self.response_ok(
            data=self.serializer(campaign.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def put(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data

        with transaction.atomic():
            self._update_campaign(request, campaign, settings)
            self._handle_campaign_goals(request, campaign, settings.get("goals", []))
            self._handle_campaign_budgets(request, campaign, settings.get("budgets", []))

        self._augment_campaign(request, campaign)
        return self.response_ok(self.serializer(campaign.settings, context={"request": request}).data)

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        account = restapi.access.get_account(request.user, settings.get("campaign", {}).get("account_id"))

        with transaction.atomic():
            new_campaign = core.models.Campaign.objects.create(
                request, account=account, name=settings.get("name"), type=settings.get("campaign", {}).get("type")
            )
            self._update_campaign(request, new_campaign, settings)
            self._handle_campaign_goals(request, new_campaign, settings.get("goals", []))
            self._handle_campaign_budgets(request, new_campaign, settings.get("budgets", []))

            prodops.hacks.apply_campaign_create_hacks(request, new_campaign)

        self._augment_campaign(request, new_campaign)
        return self.response_ok(self.serializer(new_campaign.settings, context={"request": request}).data, status=201)

    @property
    def serializer(self):
        return serializers.CampaignSerializer

    def _augment_campaign(self, request, campaign):
        campaign.settings.goals = []
        if request.user.has_perm("zemauth.can_see_campaign_goals"):
            campaign.settings.goals = self._get_campaign_goals(campaign)
        campaign.settings.budgets = []
        if request.user.has_perm("zemauth.can_see_new_budgets"):
            campaign.settings.budgets = self._get_campaign_budgets(campaign)

    def _handle_campaign_goals(self, request, campaign, data):
        if len(data) <= 0:
            raise utils.exc.ValidationError(errors={"goals_missing": ["At least one goal must be defined."]})

        campaign_goals = self._get_campaign_goals(campaign)

        goal_ids_to_delete = [x.id for x in campaign_goals if x.id not in [y.get("id") for y in data]]
        for goal_id in goal_ids_to_delete:
            dash.campaign_goals.delete_campaign_goal(request, goal_id, campaign)

        errors = []
        campaign_goals_change = False
        for item in data:
            if item.get("id") is not None:
                campaign_goal = self._get_campaign_goal(campaign_goals, item.get("id"))
                campaign_goal_updated = campaign_goal.update(request, **item)
                if campaign_goal_updated:
                    campaign_goals_change = True
                # Updating campaign goal do not
                # raise any validation errors.
                errors.append(None)
            elif len(prodops.hacks.filter_campaign_goals(campaign, [item])) == 1:
                campaign_goals_change = True
                errors.append(self._create_campaign_goal(request, campaign, item))

        if any([error is not None for error in errors]):
            raise utils.exc.ValidationError(errors={"goals": errors})

        if campaign_goals_change:
            prodops.hacks.apply_campaign_goals_change_hacks(request, campaign)

    def _handle_campaign_budgets(self, request, campaign, data):
        if request.user.has_perm("zemauth.disable_budget_management"):
            raise utils.exc.AuthorizationError()

        campaign_budgets = self._get_campaign_budgets(campaign)

        errors = []
        for item in data:
            if item.get("id") is not None:
                campaign_budget = self._get_campaign_budget(campaign_budgets, item.get("id"))
                errors.append(self._handle_campaign_budget(campaign_budget.update, request=request, **item))
            else:
                credit = self._get_credit(campaign, item.get("credit", {}).get("id"))
                errors.append(
                    self._handle_campaign_budget(
                        core.features.bcm.BudgetLineItem.objects.create,
                        request=request,
                        campaign=campaign,
                        credit=credit,
                        start_date=item.get("start_date"),
                        end_date=item.get("end_date"),
                        amount=item.get("amount"),
                        margin=item.get("margin"),
                        comment=item.get("comment"),
                    )
                )

        if any([error is not None for error in errors]):
            raise utils.exc.ValidationError(errors={"budgets": errors})

    @staticmethod
    def _get_campaign_goal(campaign_goals, goal_id) -> core.features.goals.CampaignGoal:
        campaign_goal = next((x for x in campaign_goals if x.id == goal_id), None)
        if campaign_goal is None:
            raise utils.exc.MissingDataError("Campaign goal does not exist!")
        return campaign_goal

    # TODO: should be added to core.features.goals.service
    @staticmethod
    def _get_campaign_goals(campaign):
        goals = (
            core.features.goals.CampaignGoal.objects.filter(campaign=campaign)
            .prefetch_related(
                Prefetch("values", queryset=core.features.goals.CampaignGoalValue.objects.order_by("created_dt"))
            )
            .select_related("conversion_goal")
            .order_by("id")
        )
        return goals

    @staticmethod
    @transaction.atomic
    def _create_campaign_goal(request, campaign, data):
        conversion_goal = data.get("conversion_goal")
        if conversion_goal:
            try:
                new_conversion_goal = core.features.goals.ConversionGoal.objects.create(
                    request,
                    campaign,
                    conversion_goal_type=conversion_goal.get("type"),
                    goal_id=conversion_goal.get("goal_id"),
                    conversion_window=conversion_goal.get("conversion_window"),
                )

            except core.features.goals.conversion_goal.exceptions.ConversionGoalLimitExceeded as err:
                return {"conversion_goal": [str(err)]}

            except core.features.goals.conversion_goal.exceptions.ConversionGoalNotUnique as err:
                return {"conversion_goal": [str(err)]}

            except core.features.goals.conversion_goal.exceptions.ConversionWindowRequired as err:
                return {"conversion_goal": {"conversion_window": [str(err)]}}

            except core.features.goals.conversion_goal.exceptions.ConversionPixelInvalid as err:
                return {"conversion_goal": {"goal_id": [str(err)]}}

            except core.features.goals.conversion_goal.exceptions.GoalIDInvalid as err:
                return {"conversion_goal": {"goal_id": [str(err)]}}

        try:
            core.features.goals.CampaignGoal.objects.create(
                request,
                campaign,
                goal_type=dash.constants.CampaignGoalKPI.CPA if conversion_goal else data.get("type"),
                value=data.get("value"),
                primary=data.get("primary"),
                conversion_goal=new_conversion_goal if conversion_goal else None,
            )

        except core.features.goals.campaign_goal.exceptions.ConversionGoalLimitExceeded as err:
            return {"conversion_goal": [str(err)]}

        except core.features.goals.campaign_goal.exceptions.ConversionGoalRequired as err:
            return {"conversion_goal": [str(err)]}

        except core.features.goals.campaign_goal.exceptions.MultipleSameTypeGoals as err:
            return {"type": [str(err)]}

    @staticmethod
    def _get_campaign_budgets(campaign):
        budgets = (
            core.features.bcm.BudgetLineItem.objects.filter(campaign_id=campaign.id)
            .select_related("credit")
            .order_by("-created_dt")
            .annotate_spend_data()
        )
        return [
            budget
            for budget in budgets
            if budget.state() in (dash.constants.BudgetLineItemState.PENDING, dash.constants.BudgetLineItemState.ACTIVE)
        ]

    @staticmethod
    def _get_campaign_budget(budgets, budget_id) -> core.features.bcm.BudgetLineItem:
        budget = next((x for x in budgets if x.id == budget_id), None)
        if budget is None:
            raise utils.exc.MissingDataError("Campaign budget does not exist!")
        return budget

    @staticmethod
    def _get_credit(campaign, credit_id):
        try:
            credit = core.features.bcm.CreditLineItem.objects.filter_by_account(account=campaign.account).get(
                id=credit_id
            )
        except core.features.bcm.CreditLineItem.DoesNotExist:
            raise utils.exc.MissingDataError("Credit does not exist!")
        return credit

    @staticmethod
    @transaction.atomic
    def _handle_campaign_budget(budget_update, **kwargs):
        try:
            budget_update(**kwargs)

        except utils.exc.MultipleValidationError as err:
            errors = {}
            for e in err.errors:
                if isinstance(e, core.features.bcm.exceptions.StartDateInvalid):
                    errors.setdefault("start_date", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.EndDateInvalid):
                    errors.setdefault("end_date", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.StartDateBiggerThanEndDate):
                    errors.setdefault("end_date", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.BudgetAmountCannotChange):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.BudgetAmountNegative):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.BudgetAmountExceededCreditAmount):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.BudgetAmountTooLow):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.CampaignStopDisabled):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.CanNotChangeCredit):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.CreditPending):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.CurrencyInconsistent):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.OverlappingBudgets):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.CampaignHasNoCredit):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.MarginRangeInvalid):
                    errors.setdefault("margin", []).append(str(e))

                elif isinstance(e, core.features.bcm.exceptions.OverlappingBudgetMarginInvalid):
                    errors.setdefault("margin", []).append(str(e))

            return errors

        except core.features.bcm.exceptions.CanNotChangeStartDate as err:
            return {"start_date": [str(err)]}

        except core.features.bcm.exceptions.CreditCanceled as err:
            return {"credit_id": [str(err)]}

        except core.features.bcm.exceptions.StartDateInThePast as err:
            return {"start_date": [str(err)]}

        except core.features.bcm.exceptions.EndDateInThePast as err:
            return {"end_date": [str(err)]}

        except core.features.bcm.exceptions.CanNotChangeBudget as err:
            return {"state": [str(err)]}
