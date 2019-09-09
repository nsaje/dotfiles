from django.db import transaction

import core.common
import core.features.multicurrency
import utils.k1_helper
import utils.lc_helper
from dash import constants

from . import exceptions
from . import model


class CampaignGoalManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, campaign, goal_type, value, conversion_goal=None, primary=False):
        core.common.entity_limits.enforce(model.CampaignGoal.objects.filter(campaign=campaign), campaign.account_id)
        self._validate_goal_count(campaign, goal_type)
        self._validate_cpa_goal(goal_type, conversion_goal)

        if conversion_goal is not None:
            goal_type = constants.CampaignGoalKPI.CPA

        goal = super(CampaignGoalManager, self).create(
            type=goal_type, campaign=campaign, conversion_goal=conversion_goal
        )

        history_value = goal.add_local_value(request, value, skip_history=True)
        currency_symbol = core.features.multicurrency.get_currency_symbol(goal.campaign.account.currency)

        if primary:
            goal.set_primary(request)

        import dash.campaign_goals

        if goal.type in dash.campaign_goals.COST_DEPENDANT_GOALS:
            history_value = utils.lc_helper.format_currency(history_value, places=3, curr=currency_symbol)

        campaign.write_history(
            'Added campaign goal "{}{}"'.format(
                (str(history_value) + " ") if history_value else "", constants.CampaignGoalKPI.get_text(goal.type)
            ),
            action_type=constants.HistoryActionType.GOAL_CHANGE,
            user=request.user,
        )

        utils.k1_helper.update_ad_groups(campaign.adgroup_set.all(), "campaign_goal.create")
        return goal

    def _validate_goal_count(self, campaign, goal_type):
        goals = model.CampaignGoal.objects.filter(campaign=campaign, type=goal_type)
        if goal_type == constants.CampaignGoalKPI.CPA:
            if goals.count() >= constants.MAX_CONVERSION_GOALS_PER_CAMPAIGN:
                raise exceptions.ConversionGoalLimitExceeded("Max conversion goals per campaign exceeded")
        elif goals.exists():
            raise exceptions.MultipleSameTypeGoals("Multiple goals of the same type not allowed")

    def _validate_cpa_goal(self, goal_type, conversion_goal):
        if goal_type == constants.CampaignGoalKPI.CPA and conversion_goal is None:
            raise exceptions.ConversionGoalRequired("Conversion goal required when creating a CPA goal")

    def clone(self, request, source_campaign_goal, campaign):
        conversion_goal = None
        if source_campaign_goal.conversion_goal:
            conversion_goal = core.features.goals.ConversionGoal.objects.clone(
                request, source_campaign_goal.conversion_goal, campaign
            )

        return self.create(
            request,
            campaign,
            source_campaign_goal.type,
            source_campaign_goal.get_current_value().local_value,
            conversion_goal,
            source_campaign_goal.primary,
        )
