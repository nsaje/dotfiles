import datetime
import time

from django.test import TestCase
from mock import Mock
from mock import patch

import core.models
from utils.magic_mixer import magic_mixer

from .. import CampaignStopState
from .. import constants
from ..campaign_event_processed_at import CampaignEventProcessedAt
from . import update_handler


class HandleUpdatesTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign)
        self.now = time.time()

    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_start_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_budget_updates(
        self, mock_mark_almost_depleted, mock_update_start_date, mock_update_end_date, mock_update_state
    ):

        campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=self.campaign)
        campaignstop_state.update_pending_budget_updates(True)

        update_handler.handle_updates(self.campaign.id, constants.CampaignUpdateType.BUDGET, self.now)

        self.campaign.refresh_from_db()
        mock_update_start_date.assert_called_once_with([self.campaign])
        mock_update_end_date.assert_called_once_with([self.campaign])
        mock_mark_almost_depleted.assert_called_once_with([self.campaign])
        mock_update_state.assert_called_once_with([self.campaign])
        self.assertFalse(self.campaign.campaignstopstate.pending_budget_updates)

    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_start_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_budget_daily_caps(
        self, mock_mark_almost_depleted, mock_update_start_date, mock_update_end_date, mock_update_state
    ):

        update_handler.handle_updates(self.campaign.id, constants.CampaignUpdateType.DAILY_CAP, self.now)
        mock_mark_almost_depleted.assert_called_once_with([self.campaign])

        self.assertFalse(mock_update_start_date.called)
        self.assertFalse(mock_update_end_date.called)
        self.assertFalse(mock_update_state.called)

    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_start_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_initialize(
        self, mock_mark_almost_depleted, mock_update_start_date, mock_update_end_date, mock_update_state
    ):

        update_handler.handle_updates(self.campaign.id, constants.CampaignUpdateType.INITIALIZATION, self.now)

        mock_update_start_date.assert_called_once_with([self.campaign])
        mock_update_end_date.assert_called_once_with([self.campaign])
        mock_mark_almost_depleted.assert_called_once_with([self.campaign])
        mock_update_state.assert_called_once_with([self.campaign])

    @patch("automation.campaignstop.service.update_handler.update_campaigns_state")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_end_date")
    @patch("automation.campaignstop.service.update_handler.update_campaigns_start_date")
    @patch("automation.campaignstop.service.update_handler.mark_almost_depleted_campaigns")
    def test_handle_campaignstopstate_change(
        self, mock_mark_almost_depleted, mock_update_start_date, mock_update_end_date, mock_update_state
    ):
        update_handler.handle_updates(self.campaign.id, constants.CampaignUpdateType.CAMPAIGNSTOP_STATE, self.now)
        mock_update_start_date.assert_called_once_with([self.campaign])
        self.assertFalse(mock_mark_almost_depleted.called)
        self.assertFalse(mock_update_end_date.called)
        self.assertFalse(mock_update_state.called)

    @patch("automation.campaignstop.service.update_handler._process_campaign")
    def test_handle_campaign_has_not_been_processed(self, mock_process_campaign):
        campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=self.campaign)
        campaignstop_state.update_pending_budget_updates(True)

        update_handler.handle_updates(self.campaign.id, constants.CampaignUpdateType.BUDGET, self.now)

        self.campaign.refresh_from_db()
        self.assertTrue(mock_process_campaign.called)

    @patch("automation.campaignstop.service.update_handler._process_campaign")
    def test_handle_campaign_processed_after(self, mock_process_campaign):
        campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=self.campaign)
        campaignstop_state.update_pending_budget_updates(True)

        CampaignEventProcessedAt.objects.create(campaign=self.campaign, type=constants.CampaignUpdateType.BUDGET)
        update_handler.handle_updates(
            self.campaign.id,
            constants.CampaignUpdateType.BUDGET,
            (datetime.datetime.now() - datetime.timedelta(minutes=15)).timestamp(),
        )

        self.campaign.refresh_from_db()
        self.assertFalse(mock_process_campaign.called)

    @patch("automation.campaignstop.service.update_handler._process_campaign")
    def test_handle_campaign_processed_before(self, mock_process_campaign):
        campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=self.campaign)
        campaignstop_state.update_pending_budget_updates(True)

        fifteen_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=15)
        with patch("django.utils.timezone.now", Mock(return_value=fifteen_minutes_ago)):
            CampaignEventProcessedAt.objects.create(campaign=self.campaign, type=constants.CampaignUpdateType.BUDGET)

        update_handler.handle_updates(self.campaign.id, constants.CampaignUpdateType.BUDGET, self.now)

        self.campaign.refresh_from_db()
        self.assertTrue(mock_process_campaign.called)

    @patch("automation.campaignstop.service.update_handler._process_campaign")
    def test_handle_campaign_modified_dt_updated(self, mock_process_campaign):
        campaignstop_state, _ = CampaignStopState.objects.get_or_create(campaign=self.campaign)
        campaignstop_state.update_pending_budget_updates(True)

        fifteen_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=15)

        with patch("django.utils.timezone.now", Mock(return_value=fifteen_minutes_ago)):
            campaign_event_processed = CampaignEventProcessedAt.objects.create(
                campaign=self.campaign, type=constants.CampaignUpdateType.BUDGET
            )
        self.assertEqual(campaign_event_processed.modified_dt, fifteen_minutes_ago)

        with patch("django.utils.timezone.now", Mock(return_value=datetime.datetime.fromtimestamp(self.now))):
            update_handler.handle_updates(self.campaign.id, constants.CampaignUpdateType.BUDGET, self.now)

        campaign_event_processed = CampaignEventProcessedAt.objects.get(
            campaign=self.campaign, type=constants.CampaignUpdateType.BUDGET
        )

        self.assertEqual(campaign_event_processed.modified_dt, datetime.datetime.fromtimestamp(self.now))
