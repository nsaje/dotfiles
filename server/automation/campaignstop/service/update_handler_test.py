import time

from django.test import TestCase
from mock import call
from mock import patch

import core.models
from utils.magic_mixer import magic_mixer

from .. import CampaignStopState
from .. import constants
from . import update_handler


class HandleUpdatesTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign)
        self.now = time.time()

    @patch("utils.sqs_helper.process_json_messages")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_start_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_budget_updates(
        self,
        mock_mark_almost_depleted,
        mock_update_start_date,
        mock_update_end_date,
        mock_update_state,
        mock_process_json_messages,
    ):
        messages = [{"campaign_id": self.campaign.id, "type": constants.CampaignUpdateType.BUDGET}]
        mock_process_json_messages.return_value.__enter__.return_value = messages

        campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=self.campaign)
        campaignstop_state.update_pending_budget_updates(True)

        update_handler.handle_updates()

        self.campaign.refresh_from_db()
        mock_update_start_date.assert_called_once_with([self.campaign])
        mock_update_end_date.assert_called_once_with([self.campaign])
        mock_mark_almost_depleted.assert_called_once_with([self.campaign])
        mock_update_state.assert_called_once_with([self.campaign])
        self.assertFalse(self.campaign.campaignstopstate.pending_budget_updates)

    @patch("utils.sqs_helper.process_json_messages")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_start_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_budget_daily_caps(
        self,
        mock_mark_almost_depleted,
        mock_update_start_date,
        mock_update_end_date,
        mock_update_state,
        mock_process_json_messages,
    ):
        messages = [{"campaign_id": self.campaign.id, "type": constants.CampaignUpdateType.DAILY_CAP}]
        mock_process_json_messages.return_value.__enter__.return_value = messages

        update_handler.handle_updates()
        mock_mark_almost_depleted.assert_called_once_with([self.campaign])

        self.assertFalse(mock_update_start_date.called)
        self.assertFalse(mock_update_end_date.called)
        self.assertFalse(mock_update_state.called)

    @patch("utils.sqs_helper.process_json_messages")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_start_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_initialize(
        self,
        mock_mark_almost_depleted,
        mock_update_start_date,
        mock_update_end_date,
        mock_update_state,
        mock_process_json_messages,
    ):
        messages = [{"campaign_id": self.campaign.id, "type": constants.CampaignUpdateType.INITIALIZATION}]
        mock_process_json_messages.return_value.__enter__.return_value = messages

        update_handler.handle_updates()

        mock_update_start_date.assert_called_once_with([self.campaign])
        mock_update_end_date.assert_called_once_with([self.campaign])
        mock_mark_almost_depleted.assert_called_once_with([self.campaign])
        mock_update_state.assert_called_once_with([self.campaign])

    @patch("utils.sqs_helper.process_json_messages")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_start_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_campaignstopstate_change(
        self,
        mock_mark_almost_depleted,
        mock_update_start_date,
        mock_update_end_date,
        mock_update_state,
        mock_process_json_messages,
    ):
        messages = [{"campaign_id": self.campaign.id, "type": constants.CampaignUpdateType.CAMPAIGNSTOP_STATE}]
        mock_process_json_messages.return_value.__enter__.return_value = messages

        update_handler.handle_updates()
        mock_update_start_date.assert_called_once_with([self.campaign])
        self.assertFalse(mock_mark_almost_depleted.called)
        self.assertFalse(mock_update_end_date.called)
        self.assertFalse(mock_update_state.called)

    @patch("utils.sqs_helper.process_json_messages")
    @patch("automation.campaignstop.service.update_handler.CAMPAIGNS_PER_BATCH", 6)
    @patch("automation.campaignstop.service.update_handler._time")
    @patch("automation.campaignstop.service.update_handler._process_batch")
    @patch("automation.campaignstop.service.notify")
    def test_batching(self, mock_notify, mock_process_batch, mock_time, mock_process_json_messages):
        mock_time.side_effect = [self.now, self.now + update_handler.MAX_JOB_DURATION_SECONDS + 1]
        campaigns = magic_mixer.cycle(10).blend(core.models.Campaign)
        messages = [
            {"campaign_id": campaign.id, "type": constants.CampaignUpdateType.DAILY_CAP} for campaign in campaigns
        ]
        mock_process_json_messages.return_value.__enter__.return_value = messages

        update_handler.handle_updates()
        mock_notify.assert_has_calls(
            [call(campaign, constants.CampaignUpdateType.DAILY_CAP) for campaign in campaigns[6:]]
        )
