import mock

from django.test import TestCase

import core.entity
from utils.magic_mixer import magic_mixer
from utils import dates_helper

from .. import CampaignStopState, constants
import update_campaignstop_state


class UpdateCampaignStopStateTest(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)

    @mock.patch('automation.campaignstop.service.campaign_spends.get_predicted_remaining_budget')
    def test_create_campaign_state(self, mock_get_prediction):
        mock_get_prediction.return_value = 500
        self.assertFalse(CampaignStopState.objects.filter(campaign=self.campaign).exists())

        update_campaignstop_state.update_campaigns_state(
            campaigns=[self.campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=self.campaign)
        self.assertEqual(constants.CampaignStopState.ACTIVE, campaign_stop_state.state)

    @mock.patch('utils.k1_helper.update_ad_groups', mock.MagicMock())
    @mock.patch('automation.campaignstop.service.campaign_spends.get_predicted_remaining_budget')
    def test_stop_campaign_past_max_end_date(self, mock_get_prediction):
        mock_get_prediction.return_value = 500

        today = dates_helper.local_today()
        campaign_stop_state = CampaignStopState.objects.create(
            campaign=self.campaign,
            max_allowed_end_date=dates_helper.day_before(today)
        )
        update_campaignstop_state.update_campaigns_state(
            campaigns=[self.campaign])

        campaign_stop_state.refresh_from_db()
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)

    @mock.patch('automation.campaignstop.service.campaign_spends.get_predicted_remaining_budget')
    def test_stop_campaign_with_exhausted_budget(self, mock_get_prediction):
        mock_get_prediction.return_value = 0

        campaign = magic_mixer.blend(core.entity.Campaign, real_time_campaign_stop=True)
        update_campaignstop_state.update_campaigns_state(
            campaigns=[campaign])

        campaign_stop_state = CampaignStopState.objects.get(campaign=campaign)
        self.assertEqual(constants.CampaignStopState.STOPPED, campaign_stop_state.state)
