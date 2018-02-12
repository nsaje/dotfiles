from django.test import TestCase

import dash.history_helpers
import dash.constants
from utils.magic_mixer import magic_mixer

from .model import ConversionGoal


class TestConversionGoalManager(TestCase):

    def test_create_conversion_goal_pixel(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(dash.models.Campaign, id=1)
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=campaign.account, name='mypixel')

        goal = ConversionGoal.objects.create(
            request,
            campaign,
            conversion_goal_type=dash.constants.ConversionGoalType.PIXEL,
            goal_id=pixel.id,
            conversion_window=dash.constants.ConversionWindows.LEQ_1_DAY
        )

        self.assertTrue(goal.pk)
        self.assertEqual(goal.type, dash.constants.ConversionGoalType.PIXEL)
        self.assertEqual(goal.campaign, campaign)
        self.assertEqual(goal.pixel, pixel)
        self.assertEqual(goal.name, 'mypixel 1 day')

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, request.user)
        self.assertEqual(hist.action_type, dash.constants.HistoryActionType.GOAL_CHANGE)
        self.assertEqual(hist.changes_text, 'Added conversion goal with name "mypixel 1 day" of type Conversion Pixel')
