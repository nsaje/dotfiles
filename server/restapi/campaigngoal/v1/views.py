from django.db import transaction
from django.db.models import Prefetch
from rest_framework.response import Response

import core.features.goals
import restapi.access
import utils.exc
from dash import campaign_goals
from dash import constants
from restapi.campaigngoal.v1 import serializers
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet


class CampaignGoalViewSet(RESTAPIBaseViewSet):
    def get(self, request, campaign_id, goal_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        goal = self._get_campaign_goal(campaign, goal_id)
        return self.response_ok(serializers.CampaignGoalSerializer(goal).data)

    def put(self, request, campaign_id, goal_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        serializer = serializers.CampaignGoalSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        goal = self._get_campaign_goal(campaign, goal_id)
        goal.update(request, **serializer.validated_data)
        return self.response_ok(serializers.CampaignGoalSerializer(goal).data)

    def remove(self, request, campaign_id, goal_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        goal = self._get_campaign_goal(campaign, goal_id)
        campaign_goals.delete_campaign_goal(request, goal.id, campaign)
        return Response(None, status=204)

    def list(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        goals = self._get_campaign_goals_list(campaign)
        paginator = StandardPagination()
        goals_paginated = paginator.paginate_queryset(goals, request)
        return paginator.get_paginated_response(serializers.CampaignGoalSerializer(goals_paginated, many=True).data)

    def create(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        serializer = serializers.CampaignGoalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        new_goal = self._create_goal(request, campaign, data)
        return self.response_ok(serializers.CampaignGoalSerializer(new_goal).data, status=201)

    @staticmethod
    def _get_campaign_goal(campaign, goal_id):
        try:
            goal = core.features.goals.CampaignGoal.objects.get(campaign=campaign, pk=goal_id)
        except core.features.goals.CampaignGoal.DoesNotExist:
            raise utils.exc.MissingDataError("Campaign goal does not exist!")
        return goal

    @staticmethod
    def _get_campaign_goals_list(campaign):
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
                goal_type=constants.CampaignGoalKPI.CPA if conversion_goal else data.get("type"),
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
