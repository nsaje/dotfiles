import core.models
import dash.constants
import dash.history_helpers
from utils.base_test_case import FutureBaseTestCase
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from .model import ConversionGoal


class ConversionGoalManagerTestCase(FutureBaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(self.user)
        self.account = self.mix_account(self.request.user, permissions=[Permission.READ, Permission.WRITE])

    def test_create_conversion_goal_pixel(self):

        campaign = magic_mixer.blend(core.models.Campaign, id=1, account=self.account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=campaign.account, name="mypixel")

        goal = ConversionGoal.objects.create(
            self.request,
            campaign,
            conversion_goal_type=dash.constants.ConversionGoalType.PIXEL,
            goal_id=pixel.id,
            conversion_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )

        self.assertTrue(goal.pk)
        self.assertEqual(goal.type, dash.constants.ConversionGoalType.PIXEL)
        self.assertEqual(goal.campaign, campaign)
        self.assertEqual(goal.pixel, pixel)
        self.assertEqual(goal.name, "mypixel 1 day")

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, self.request.user)
        self.assertEqual(hist.action_type, dash.constants.HistoryActionType.GOAL_CHANGE)
        self.assertEqual(hist.changes_text, 'Added conversion goal with name "mypixel 1 day" of type Conversion Pixel')

    def test_clone_conversion_goal_pixel(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, id=1, account=account)
        cloned_campaign = magic_mixer.blend(core.models.Campaign, id=2, account=account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="mypixel")

        goal = ConversionGoal.objects.create(
            self.request,
            campaign,
            conversion_goal_type=dash.constants.ConversionGoalType.PIXEL,
            goal_id=pixel.id,
            conversion_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )

        self.assertTrue(goal.pk)
        self.assertEqual(goal.type, dash.constants.ConversionGoalType.PIXEL)
        self.assertEqual(goal.campaign, campaign)
        self.assertEqual(goal.pixel, pixel)
        self.assertEqual(goal.name, "mypixel 1 day")

        hist = dash.history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(hist.created_by, self.request.user)
        self.assertEqual(hist.action_type, dash.constants.HistoryActionType.GOAL_CHANGE)
        self.assertEqual(hist.changes_text, 'Added conversion goal with name "mypixel 1 day" of type Conversion Pixel')

        cloned_goal = ConversionGoal.objects.clone(self.request, goal, cloned_campaign)

        self.assertTrue(cloned_goal.pk)
        self.assertNotEqual(goal.pk, cloned_goal.pk)
        self.assertEqual(cloned_campaign, cloned_goal.campaign)
        self.assertEqual(goal.type, cloned_goal.type)
        self.assertEqual(goal.pixel, cloned_goal.pixel)
        self.assertEqual(goal.name, cloned_goal.name)

        hist = dash.history_helpers.get_campaign_history(cloned_campaign).first()
        self.assertEqual(hist.created_by, self.request.user)
        self.assertEqual(hist.action_type, dash.constants.HistoryActionType.GOAL_CHANGE)
        self.assertEqual(hist.changes_text, 'Added conversion goal with name "mypixel 1 day" of type Conversion Pixel')
