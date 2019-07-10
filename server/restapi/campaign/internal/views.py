import rest_framework.permissions
import rest_framework.serializers
from django.db import transaction
from django.db.models import Prefetch

import core.features.bcm
import core.features.goals
import core.models
import dash.campaign_goals
import dash.constants
import restapi.access
import restapi.campaign.v1.views
import utils.exc

from . import helpers
from . import serializers


class CampaignViewSet(restapi.campaign.v1.views.CampaignViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)

    def validate(self, request):
        serializer = serializers.CampaignSerializer(data=request.data, partial=True, context={"request": request})
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
            data=serializers.CampaignSerializer(campaign.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id, select_related=True)
        self._augment_campaign(request, campaign)
        extra_data = helpers.get_extra_data(request.user, campaign)
        return self.response_ok(
            data=serializers.CampaignSerializer(campaign.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def put(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        serializer = serializers.CampaignSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data

        with transaction.atomic():
            # TODO: hacks.apply_set_goals_hacks
            # TODO: hacks.override_campaign_settings_form_data
            self._update_campaign(request, campaign, settings)
            self._handle_goals(request, campaign, settings.get("goals", []))
            # TODO: hacks.apply_campaign_change_hacks

        self._augment_campaign(request, campaign)
        return self.response_ok(serializers.CampaignSerializer(campaign.settings, context={"request": request}).data)

    def create(self, request):
        serializer = serializers.CampaignSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        settings = serializer.validated_data
        account = restapi.access.get_account(request.user, settings.get("campaign", {}).get("account_id"))

        with transaction.atomic():
            new_campaign = core.models.Campaign.objects.create(
                request, account=account, name=settings.get("name"), type=settings.get("campaign", {}).get("type")
            )
            # TODO: hacks.apply_set_goals_hacks
            # TODO: hacks.override_campaign_settings_form_data
            self._update_campaign(request, new_campaign, settings)
            self._handle_goals(request, new_campaign, settings.get("goals", []))
            # TODO: hacks.apply_campaign_change_hacks

        self._augment_campaign(request, new_campaign)
        return self.response_ok(
            serializers.CampaignSerializer(new_campaign.settings, context={"request": request}).data, status=201
        )

    def _augment_campaign(self, request, campaign):
        campaign.settings.goals = []
        if request.user.has_perm("zemauth.can_see_campaign_goals"):
            campaign.settings.goals = self._get_campaign_goals(campaign)
        campaign.settings.budgets = []
        if request.user.has_perm("zemauth.can_see_new_budgets"):
            campaign.settings.budgets = self._get_active_budgets(campaign)

    def _handle_goals(self, request, campaign, data):
        if len(data) <= 0:
            raise utils.exc.ValidationError(errors={"goals_missing": ["At least one goal must be defined."]})

        campaign_goals = self._get_campaign_goals(campaign)
        data_to_create = [x for x in data if x.get("id") is None]
        data_to_update = [x for x in data if x.get("id") is not None]
        goal_ids_to_delete = [x.id for x in campaign_goals if x.id not in [y.get("id") for y in data_to_update]]

        for goal_id in goal_ids_to_delete:
            # TODO: should be refactored to core.features.goals.service
            dash.campaign_goals.delete_campaign_goal(request, goal_id, campaign)

        for item in data_to_update:
            campaign_goal = self._get_campaign_goal(campaign_goals, item.get("id"))
            campaign_goal.update(request, **item)

        for item in data_to_create:
            self._create_goal(request, campaign, item)

    @staticmethod
    def _get_campaign_goal(campaign_goals, goal_id):
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

    # TODO: should be added to core.features.goals.service
    @staticmethod
    @transaction.atomic
    def _create_goal(request, campaign, data):
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
                raise utils.exc.ValidationError(errors={"conversionGoal": [str(err)]})

            except core.features.goals.conversion_goal.exceptions.ConversionWindowRequired as err:
                raise utils.exc.ValidationError(errors={"conversionGoal": {"conversionWindow": [str(err)]}})

            except core.features.goals.conversion_goal.exceptions.ConversionPixelInvalid as err:
                raise utils.exc.ValidationError(errors={"conversionGoal": {"goalId": [str(err)]}})

            except core.features.goals.conversion_goal.exceptions.ConversionGoalNotUnique as err:
                raise utils.exc.ValidationError(errors={"conversionGoal": [str(err)]})

            except core.features.goals.conversion_goal.exceptions.GoalIDInvalid as err:
                raise utils.exc.ValidationError(errors={"conversionGoal": {"goalId": [str(err)]}})

        try:
            new_goal = core.features.goals.CampaignGoal.objects.create(
                request,
                campaign,
                goal_type=dash.constants.CampaignGoalKPI.CPA if conversion_goal else data.get("type"),
                value=data.get("value"),
                primary=data.get("primary"),
                conversion_goal=new_conversion_goal if conversion_goal else None,
            )

        except core.features.goals.campaign_goal.exceptions.ConversionGoalLimitExceeded as err:
            raise utils.exc.ValidationError(str(err))

        except core.features.goals.campaign_goal.exceptions.MultipleSameTypeGoals as err:
            raise utils.exc.ValidationError(errors={"type": [str(err)]})

        except core.features.goals.campaign_goal.exceptions.ConversionGoalRequired as err:
            raise utils.exc.ValidationError(errors={"conversionGoal": [str(err)]})

        return new_goal

    @staticmethod
    def _get_active_budgets(campaign):
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
