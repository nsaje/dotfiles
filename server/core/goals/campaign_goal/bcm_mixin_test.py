import decimal

from django.test import TestCase

from .model import CampaignGoal

import core.entity
from dash import campaign_goals
from dash import constants
from utils.magic_mixer import magic_mixer


class CampaignGoalBCMMixinTest(TestCase):
    def setUp(self):
        campaign = magic_mixer.blend(core.entity.Campaign)

        cost_types = campaign_goals.COST_DEPENDANT_GOALS
        self.campaign_goals_migrated = magic_mixer.cycle(len(cost_types)).blend(
            CampaignGoal,
            campaign=campaign,
            type=(typ for typ in cost_types)
        )

        other_types = set(constants.CampaignGoalKPI.get_all()) - set(cost_types)
        self.campaign_goals_skipped = magic_mixer.cycle(len(other_types)).blend(
            CampaignGoal,
            campaign=campaign,
            type=(typ for typ in other_types)
        )

        for campaign_goal in self.campaign_goals_migrated:
            campaign_goal.add_value(None, decimal.Decimal('2.0'), skip_history=True)

        for campaign_goal in self.campaign_goals_skipped:
            campaign_goal.add_value(None, decimal.Decimal('2.0'), skip_history=True)

    def test_migrate_to_bcm_v2(self):
        request = magic_mixer.blend_request_user()
        for campaign_goal in self.campaign_goals_migrated:
            campaign_goal.migrate_to_bcm_v2(request, decimal.Decimal('0.2'), decimal.Decimal('0.1'))
            self.assertEqual(decimal.Decimal('2.778'), campaign_goal.get_current_value().value)

        for campaign_goal in self.campaign_goals_skipped:
            campaign_goal.migrate_to_bcm_v2(request, decimal.Decimal('0.2'), decimal.Decimal('0.1'))
            self.assertEqual(decimal.Decimal('2.0'), campaign_goal.get_current_value().value)
