import celery.exceptions
import rest_framework.permissions
import rest_framework.serializers
from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch

import core.features.bcm
import core.features.bcm.exceptions
import core.features.goals
import core.models
import dash.campaign_goals
import dash.constants
import dash.features.alerts
import dash.features.clonecampaign.exceptions
import dash.features.clonecampaign.service
import dash.views.navigation_helpers
import prodops.hacks
import restapi.campaign.v1.views
import restapi.serializers.alert
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from zemauth.features.entity_permission import Permission

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
        qpe = serializers.CampaignInternalQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        account_id = qpe.validated_data.get("account_id")
        account = zemauth.access.get_account(request.user, Permission.WRITE, account_id)
        campaign = core.models.Campaign.objects.get_default(request, account)
        self._augment_campaign(request, campaign)
        extra_data = helpers.get_extra_data(request.user, campaign)
        return self.response_ok(
            data=self.serializer(campaign.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, campaign_id):
        campaign = zemauth.access.get_campaign(request.user, Permission.READ, campaign_id)
        self._augment_campaign(request, campaign)
        extra_data = helpers.get_extra_data(request.user, campaign)
        return self.response_ok(
            data=self.serializer(campaign.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def list(self, request):
        qpe = serializers.CampaignListQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        account_id = qpe.validated_data.get("account_id")
        agency_id = qpe.validated_data.get("agency_id")

        if account_id:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            campaigns_qs = core.models.Campaign.objects.filter(account=account)
        elif agency_id:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            campaigns_qs = core.models.Campaign.objects.filter(account__agency=agency)
        else:
            raise utils.exc.ValidationError("Either agency id or account id must be provided.")

        keyword = qpe.validated_data.get("keyword")
        if keyword:
            campaigns_qs = campaigns_qs.filter(settings__name__icontains=keyword)

        paginator = StandardPagination()

        campaigns_qs = campaigns_qs.select_related("settings").order_by("pk")

        campaigns_paginated = paginator.paginate_queryset(campaigns_qs, request)
        paginated_settings = [ad.settings for ad in campaigns_paginated]
        return paginator.get_paginated_response(
            self.serializer(paginated_settings, many=True, context={"request": request}).data
        )

    def alerts(self, request, campaign_id):
        qpe = restapi.serializers.alert.AlertQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        campaign = zemauth.access.get_campaign(request.user, Permission.READ, campaign_id)
        alerts = dash.features.alerts.get_campaign_alerts(request, campaign, **qpe.validated_data)

        return self.response_ok(
            data=restapi.serializers.alert.AlertSerializer(alerts, many=True, context={"request": request}).data
        )

    def put(self, request, campaign_id):
        campaign = zemauth.access.get_campaign(request.user, Permission.WRITE, campaign_id)
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data

        with transaction.atomic():
            self._update_campaign(request, campaign, settings)
            if "goals" in settings.keys():
                self._handle_campaign_goals(request, campaign, settings.get("goals", []))
            if "budgets" in settings.keys():
                self._handle_campaign_budgets(request, campaign, settings.get("budgets", []))
            if "deals" in settings.keys():
                self._handle_deals(request, campaign, settings.get("deals", []))

        self._augment_campaign(request, campaign)
        return self.response_ok(self.serializer(campaign.settings, context={"request": request}).data)

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        account = zemauth.access.get_account(
            request.user, Permission.WRITE, settings.get("campaign", {}).get("account_id")
        )

        with transaction.atomic():
            new_campaign = core.models.Campaign.objects.create(
                request, account=account, name=settings.get("name"), type=settings.get("campaign", {}).get("type")
            )
            self._update_campaign(request, new_campaign, settings)
            self._handle_campaign_goals(request, new_campaign, settings.get("goals", []))
            self._handle_campaign_budgets(request, new_campaign, settings.get("budgets", []))
            self._handle_deals(request, new_campaign, settings.get("deals", []))

            prodops.hacks.apply_campaign_create_hacks(request, new_campaign)

        self._augment_campaign(request, new_campaign)
        return self.response_ok(self.serializer(new_campaign.settings, context={"request": request}).data, status=201)

    def clone(self, request, campaign_id):
        if not request.user.has_perm("zemauth.can_clone_campaigns"):
            raise utils.exc.AuthorizationError()

        serializer = serializers.CloneCampaignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        campaign = zemauth.access.get_campaign(request.user, Permission.WRITE, campaign_id)

        if settings.USE_CELERY_FOR_CAMPAIGN_CLONING:
            result = dash.features.clonecampaign.service.clone_async.delay(
                request.user,
                source_campaign_name=campaign.name,
                source_campaign_id=campaign.id,
                send_email=True,
                **data
            )
            try:
                cloned_campaign_id = result.get(timeout=10)
                cloned_campaign = zemauth.access.get_campaign(request.user, Permission.WRITE, cloned_campaign_id)
            except celery.exceptions.TimeoutError:
                return self.response_ok(None)
        else:
            try:
                cloned_campaign = dash.features.clonecampaign.service.clone(request, campaign, **data)
            except dash.features.clonecampaign.exceptions.CanNotCloneAds as error:
                raise utils.exc.ValidationError(error)

        return self.response_ok(
            self.serializer(cloned_campaign.settings, context={"request": request}).data, status=201
        )

    @property
    def serializer(self):
        return serializers.CampaignSerializer

    def _augment_campaign(self, request, campaign):
        campaign.settings.goals = []
        if request.user.has_perm("zemauth.can_see_campaign_goals"):
            campaign.settings.goals = self._get_campaign_goals(campaign)
        campaign.settings.budgets = self._get_campaign_budgets(campaign)
        campaign.settings.deals = []
        if request.user.has_perm("zemauth.can_see_direct_deals_section"):
            campaign.settings.deals = campaign.get_deals(request)

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
        if not request.user.has_budget_perm_on(
            campaign, fallback_permission="zemauth.disable_budget_management", negate_fallback_permission=True
        ):
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

    @staticmethod
    def _handle_deals(request, campaign, data):
        errors = []
        new_deals = []

        for item in data:
            if item.get("id") is not None:
                try:
                    new_deals.append(zemauth.access.get_direct_deal(request.user, Permission.READ, item.get("id")))
                    errors.append(None)
                except utils.exc.MissingDataError as err:
                    errors.append({"id": [str(err)]})
            else:
                new_deal = core.features.deals.DirectDeal.objects.create(
                    request,
                    account=campaign.account,
                    source=item.get("source"),
                    deal_id=item.get("deal_id"),
                    name=item.get("name"),
                )
                new_deal.update(request, **item)
                new_deals.append(new_deal)
                errors.append(None)

        if any([error is not None for error in errors]):
            raise utils.exc.ValidationError(errors={"deals": errors})

        new_deals_set = set(new_deals)

        deals = campaign.get_deals(request)
        deals_set = set(deals)

        to_be_removed = deals_set.difference(new_deals_set)
        to_be_added = new_deals_set.difference(deals_set)

        if to_be_removed or to_be_added:
            campaign.remove_deals(request, list(to_be_removed))
            campaign.add_deals(request, list(to_be_added))
