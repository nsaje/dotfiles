from decimal import Decimal

from django.test import TestCase
from mock import patch

import core.features.multicurrency
import core.models
import dash.constants
import dash.history_helpers
from utils.magic_mixer import magic_mixer

from ..campaign_goal_value import CampaignGoalValue
from . import exceptions
from .model import CampaignGoal


class TestCampaignGoals(TestCase):
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

    def test_set_primary(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(core.models.Campaign)
        goal1 = magic_mixer.blend(CampaignGoal, campaign=campaign, primary=True)
        goal2 = magic_mixer.blend(CampaignGoal, campaign=campaign, primary=False)

        goal2.set_primary(request)

        goal1.refresh_from_db()
        goal2.refresh_from_db()
        self.assertFalse(goal1.primary)
        self.assertTrue(goal2.primary)

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(dash.constants.HistoryActionType.GOAL_CHANGE, hist.action_type)
        self.assertEqual('Campaign goal "Time on Site - Seconds" set as primary', hist.changes_text)

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_add_value(self, mock_get_exchange_rate):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(core.models.Campaign)
        goal = magic_mixer.blend(CampaignGoal, campaign=campaign)
        mock_get_exchange_rate.return_value = Decimal("2.0")
        CampaignGoalValue.objects.create(value=Decimal("10"), local_value=Decimal("10"), campaign_goal=goal)

        goal.add_value(request, Decimal("15"))
        goal.add_local_value(request, Decimal("40"))

        self.assertEqual(
            [val.value for val in CampaignGoalValue.objects.all()], [Decimal("10"), Decimal("15"), Decimal("40")]
        )

        self.assertEqual(
            [val.local_value for val in CampaignGoalValue.objects.all()], [Decimal("10"), Decimal("15"), Decimal("40")]
        )

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(dash.constants.HistoryActionType.GOAL_CHANGE, hist.action_type)
        self.assertEqual(hist.changes_text, 'Changed campaign goal value: "40 Time on Site - Seconds"')

    @patch.object(core.features.multicurrency, "get_current_exchange_rate")
    def test_add_value_cost_dependant_goal(self, mock_get_exchange_rate):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(core.models.Campaign)
        goal = magic_mixer.blend(CampaignGoal, campaign=campaign, type=dash.constants.CampaignGoalKPI.CPC)
        mock_get_exchange_rate.return_value = Decimal("2.0")
        CampaignGoalValue.objects.create(value=Decimal("1"), local_value=Decimal("2"), campaign_goal=goal)

        goal.add_value(request, Decimal("1.5"))
        goal.add_local_value(request, Decimal("4"))

        self.assertEqual(
            [val.value for val in CampaignGoalValue.objects.all()], [Decimal("1"), Decimal("1.5"), Decimal("2")]
        )

        self.assertEqual(
            [val.local_value for val in CampaignGoalValue.objects.all()], [Decimal("2"), Decimal("3"), Decimal("4")]
        )

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(dash.constants.HistoryActionType.GOAL_CHANGE, hist.action_type)
        self.assertEqual(hist.changes_text, 'Changed campaign goal value: "$4.000 CPC"')

    def test_create_cpa_goal_with_no_conversion_goal(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(core.models.Campaign, id=1)

        with self.assertRaises(exceptions.ConversionGoalRequired):
            CampaignGoal.objects.create(request, campaign, goal_type=dash.constants.CampaignGoalKPI.CPA, value=1.0)
