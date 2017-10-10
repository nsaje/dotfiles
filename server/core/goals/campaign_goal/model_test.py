from decimal import Decimal
from django.test import TestCase

import dash.models
import dash.history_helpers
import dash.constants
from utils.magic_mixer import magic_mixer

from model import CampaignGoal
from ..campaign_goal_value import CampaignGoalValue


class TestCampaignGoals(TestCase):

    def test_create_campaign_goal(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(dash.models.Campaign, id=1)

        goal = CampaignGoal.objects.create(
            request,
            campaign,
            goal_type=1,
            value=1.0
        )

        self.assertTrue(goal.pk)
        self.assertEqual(goal.type, 1)
        self.assertEqual(goal.campaign_id, 1)

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(dash.constants.HistoryActionType.GOAL_CHANGE, hist.action_type)
        self.assertEqual(hist.changes_text, 'Added campaign goal "1.0 Time on Site - Seconds"')

    def test_set_primary(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(dash.models.Campaign)
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

    def test_add_value(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(dash.models.Campaign)
        goal = magic_mixer.blend(CampaignGoal, campaign=campaign)
        CampaignGoalValue.objects.create(
            value=Decimal('10'),
            campaign_goal=goal,
        )

        goal.add_value(request, Decimal('15'))

        self.assertEqual(
            [val.value for val in CampaignGoalValue.objects.all()],
            [Decimal('10'), Decimal('15')]
        )

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(dash.constants.HistoryActionType.GOAL_CHANGE, hist.action_type)
        self.assertEqual(hist.changes_text, 'Changed campaign goal value: "15 Time on Site - Seconds"')
