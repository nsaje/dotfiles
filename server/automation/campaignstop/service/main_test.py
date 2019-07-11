import decimal

import mock
from django.test import TestCase

import core.models
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .. import CampaignStopState
from .. import constants
from . import config
from . import main


class UpdateCampaignStopStateTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)
        self._prepare_update_notifier_mock()
        self._prepare_threadpoolexecutor_mock()

    def _prepare_update_notifier_mock(self):
        notify_patcher = mock.patch("automation.campaignstop.service.update_notifier.notify_campaignstopstate_change")
        notify_patcher.start()
        self.addCleanup(notify_patcher.stop)

    def _prepare_threadpoolexecutor_mock(self):
        # NOTE: Code ran in a separate thread would use a separate transaction which would make testing hard. In order
        # to avoid this we use sequential map instead of threads to produce results.
        def _eager_map(fun, iter_):
            return list(map(fun, iter_))

        patcher = mock.patch("concurrent.futures.ThreadPoolExecutor")
        mock_threadpoolexecutor = patcher.start()

        mock_threadpoolexecutor.return_value.__enter__.return_value.map = _eager_map
        self.addCleanup(patcher.stop)

    @mock.patch("automation.campaignstop.service.spends_helper.get_predicted_remaining_budget")
    def test_create_campaign_state(self, mock_get_prediction):
        self._prepare_threadpoolexecutor_mock()
        mock_get_prediction.return_value = config.THRESHOLD * 2
        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).exists())

        main.update_campaigns_state(campaigns=[self.campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(constants.CampaignStopState.ACTIVE, campaign_stop_state.state)

    @mock.patch("automation.campaignstop.service.spends_helper.get_predicted_remaining_budget")
    def test_dont_start_campaign_slightly_above_threshold(self, mock_get_prediction):
        mock_get_prediction.return_value = config.THRESHOLD * decimal.Decimal("1.2")
        main.update_campaigns_state(campaigns=[self.campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)

    @mock.patch("utils.k1_helper.update_ad_groups", mock.MagicMock())
    @mock.patch("automation.campaignstop.service.spends_helper.get_predicted_remaining_budget")
    def test_stop_campaign_past_max_end_date(self, mock_get_prediction):
        mock_get_prediction.return_value = 500

        today = dates_helper.local_today()
        campaign_stop_state = CampaignStopState.objects.create(
            campaign=self.campaign, max_allowed_end_date=dates_helper.day_before(today)
        )
        main.update_campaigns_state(campaigns=[self.campaign])

        campaign_stop_state.refresh_from_db()
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)

    @mock.patch("automation.campaignstop.service.spends_helper.get_predicted_remaining_budget")
    def test_stop_campaign_with_exhausted_budget(self, mock_get_prediction):
        mock_get_prediction.return_value = 0

        campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)
        main.update_campaigns_state(campaigns=[campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=campaign)
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)
