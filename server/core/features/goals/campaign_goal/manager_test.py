from django.test import TestCase

import core.models
import dash.constants
import dash.history_helpers
from utils.magic_mixer import magic_mixer

from ..conversion_goal import ConversionGoal
from . import exceptions
from .model import CampaignGoal


class TestConversionGoalManager(TestCase):
    def test_create_campaign_goal(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(core.models.Campaign, id=1)

        goal = CampaignGoal.objects.create(request, campaign, goal_type=1, value=1.0)

        self.assertTrue(goal.pk)
        self.assertEqual(goal.type, 1)
        self.assertEqual(goal.campaign_id, 1)

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(dash.constants.HistoryActionType.GOAL_CHANGE, hist.action_type)
        self.assertEqual(hist.changes_text, 'Added campaign goal "1 Time on Site - Seconds"')

    def test_create_campaign_goal_with_conversion_goal(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(core.models.Campaign, id=1)

        conversion_goal = ConversionGoal.objects.create(
            request,
            campaign,
            conversion_goal_type=dash.constants.ConversionGoalType.GA,
            goal_id="goal name",
            conversion_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )
        campaign_goal = CampaignGoal.objects.create(
            request,
            campaign,
            goal_type=dash.constants.ConversionGoalType.GA,
            value=1.0,
            conversion_goal=conversion_goal,
            primary=True,
        )

        self.assertTrue(campaign_goal.pk)
        self.assertEqual(campaign_goal.campaign, campaign)
        self.assertEqual(campaign_goal.type, dash.constants.CampaignGoalKPI.CPA)
        self.assertTrue(campaign_goal.primary)
        self.assertEqual(campaign_goal.get_current_value().value, 1.0)
        self.assertEqual(conversion_goal, campaign_goal.conversion_goal)

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(hist.action_type, dash.constants.HistoryActionType.GOAL_CHANGE)
        self.assertEqual(hist.changes_text, 'Added campaign goal "$1.000 $CPA"')

    def test_create_cpa_goal_with_no_conversion_goal(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(core.models.Campaign, id=1)

        with self.assertRaises(exceptions.ConversionGoalRequired):
            CampaignGoal.objects.create(request, campaign, goal_type=dash.constants.CampaignGoalKPI.CPA, value=1.0)

    def test_clone_campaign_goal_with_conversion_goal(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(core.models.Campaign, id=1)
        cloned_campaign = magic_mixer.blend(core.models.Campaign, id=2)

        conversion_goal = ConversionGoal.objects.create(
            request,
            campaign,
            conversion_goal_type=dash.constants.ConversionGoalType.GA,
            goal_id="goal name",
            conversion_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )
        campaign_goal = CampaignGoal.objects.create(
            request,
            campaign,
            goal_type=dash.constants.ConversionGoalType.GA,
            value=1.0,
            conversion_goal=conversion_goal,
            primary=True,
        )

        self.assertTrue(campaign_goal.pk)
        self.assertEqual(campaign_goal.campaign, campaign)
        self.assertEqual(campaign_goal.type, dash.constants.CampaignGoalKPI.CPA)
        self.assertTrue(campaign_goal.primary)
        self.assertEqual(campaign_goal.get_current_value().value, 1.0)
        self.assertEqual(conversion_goal, campaign_goal.conversion_goal)

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(hist.action_type, dash.constants.HistoryActionType.GOAL_CHANGE)
        self.assertEqual(hist.changes_text, 'Added campaign goal "$1.000 $CPA"')

        cloned_campaign_goal = CampaignGoal.objects.clone(request, campaign_goal, cloned_campaign)

        self.assertTrue(cloned_campaign_goal.pk)
        self.assertNotEqual(campaign_goal.pk, cloned_campaign_goal.pk)
        self.assertEqual(cloned_campaign, cloned_campaign_goal.campaign)
        self.assertEqual(campaign_goal.type, cloned_campaign_goal.type)
        self.assertTrue(cloned_campaign_goal.primary)
        self.assertEqual(campaign_goal.get_current_value().value, cloned_campaign_goal.get_current_value().value)

        self.assertNotEqual(campaign_goal.conversion_goal.pk, cloned_campaign_goal.conversion_goal.pk)
        self.assertEqual(cloned_campaign, cloned_campaign_goal.conversion_goal.campaign)
        self.assertEqual(campaign_goal.conversion_goal.type, cloned_campaign_goal.conversion_goal.type)
        self.assertEqual(campaign_goal.conversion_goal.name, cloned_campaign_goal.conversion_goal.name)
        self.assertEqual(campaign_goal.conversion_goal.pixel, cloned_campaign_goal.conversion_goal.pixel)
        self.assertEqual(
            campaign_goal.conversion_goal.conversion_window, cloned_campaign_goal.conversion_goal.conversion_window
        )
        self.assertEqual(campaign_goal.conversion_goal.goal_id, cloned_campaign_goal.conversion_goal.goal_id)

        hist = dash.history_helpers.get_campaign_history(cloned_campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(hist.action_type, dash.constants.HistoryActionType.GOAL_CHANGE)
        self.assertEqual(hist.changes_text, 'Added campaign goal "$1.000 $CPA"')
