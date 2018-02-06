from mock import patch

from django.test import TestCase

import core.entity
import core.entity.settings
from utils.magic_mixer import magic_mixer

from .. import constants
import update_notifier


class AdGroupSettingsNotifyTest(TestCase):

    def setUp(self):
        self.ad_group = magic_mixer.blend(core.entity.AdGroup)
        self.notify_fields = {'state', 'b1_sources_group_state', 'b1_sources_group_daily_budget'}

    @patch('utils.sqs_helper.write_message_json')
    def test_no_notify(self, mock_write_message):
        all_fields = set(core.entity.settings.AdGroupSettings._settings_fields)
        no_notify_fields = all_fields - self.notify_fields

        for field in no_notify_fields:
            update_notifier.notify_ad_group_settings_change(
                self.ad_group.settings, {field: 'New value'})
            self.assertFalse(mock_write_message.called)

    @patch('utils.sqs_helper.write_message_json')
    @patch('django.conf.settings.CAMPAIGN_STOP_UPDATE_HANDLER_QUEUE', 'test-queue')
    def test_notify(self, mock_write_message):
        for field in self.notify_fields:
            mock_write_message.reset_mock()

            update_notifier.notify_ad_group_settings_change(
                self.ad_group.settings, {'state': 1})
            mock_write_message.assert_called_with('test-queue', {
                'campaign_id': self.ad_group.campaign_id,
                'type': constants.CampaignUpdateType.DAILY_CAP
            })


class AdGroupSourceSettingsNotifyTest(TestCase):

    def setUp(self):
        self.ad_group_source = magic_mixer.blend(core.entity.AdGroupSource)
        self.notify_fields = {'state', 'daily_budget_cc'}

    @patch('utils.sqs_helper.write_message_json')
    def test_no_notify(self, mock_write_message):
        all_fields = set(core.entity.settings.AdGroupSourceSettings._settings_fields)
        no_notify_fields = all_fields - self.notify_fields
        for field in no_notify_fields:
            update_notifier.notify_ad_group_source_settings_change(
                self.ad_group_source.settings, {field: 'New value'})
            self.assertFalse(mock_write_message.called)

    @patch('utils.sqs_helper.write_message_json')
    @patch('django.conf.settings.CAMPAIGN_STOP_UPDATE_HANDLER_QUEUE', 'test-queue')
    def test_notify(self, mock_write_message):
        for field in self.notify_fields:
            mock_write_message.reset_mock()

            update_notifier.notify_ad_group_source_settings_change(
                self.ad_group_source.settings, {field: 'New value'})
            mock_write_message.assert_called_with('test-queue', {
                'campaign_id': self.ad_group_source.ad_group.campaign_id,
                'type': constants.CampaignUpdateType.DAILY_CAP
            })


class BudgetLineItemNotifyTest(TestCase):

    def setUp(self):
        self.campaign = magic_mixer.blend(core.entity.Campaign)

    @patch('utils.sqs_helper.write_message_json')
    @patch('django.conf.settings.CAMPAIGN_STOP_UPDATE_HANDLER_QUEUE', 'test-queue')
    def test_notify(self, mock_write_message):
        update_notifier.notify_budget_line_item_change(self.campaign)
        mock_write_message.assert_called_with('test-queue', {
            'campaign_id': self.campaign.id,
            'type': constants.CampaignUpdateType.BUDGET
        })
