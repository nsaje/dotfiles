from django.test import TestCase
from mock import patch

import core.models
from utils.magic_mixer import magic_mixer

from . import update_handler
from .. import constants


class HandleUpdatesTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign)

    @patch("utils.sqs_helper.process_json_messages")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_budget_updates(
        self, mock_mark_almost_depleted, mock_update_end_date, mock_update_state, mock_process_json_messages
    ):
        messages = [{"campaign_id": self.campaign.id, "type": constants.CampaignUpdateType.BUDGET}]
        mock_process_json_messages.return_value.__enter__.return_value = messages

        update_handler.handle_updates()

        self.assertTrue(mock_update_end_date.called)
        self.assertTrue(mock_mark_almost_depleted.called)
        self.assertTrue(mock_update_state.called)

    @patch("utils.sqs_helper.process_json_messages")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_budget_daily_caps(
        self, mock_mark_almost_depleted, mock_update_end_date, mock_update_state, mock_process_json_messages
    ):
        messages = [{"campaign_id": self.campaign.id, "type": constants.CampaignUpdateType.DAILY_CAP}]
        mock_process_json_messages.return_value.__enter__.return_value = messages

        update_handler.handle_updates()
        self.assertTrue(mock_mark_almost_depleted.called)

        self.assertFalse(mock_update_end_date.called)
        self.assertFalse(mock_update_state.called)
