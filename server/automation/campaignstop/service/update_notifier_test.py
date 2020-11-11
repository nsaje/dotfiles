from django.test import TestCase
from django.test import override_settings
from mock import patch

import core.models
import core.models.settings
from utils.magic_mixer import magic_mixer

from .. import constants
from . import update_notifier


class AdGroupSettingsNotifyTest(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__real_time_campaign_stop=True)
        self.notify_fields = set(update_notifier.AD_GROUP_SETTINGS_FIELDS)

    @patch("utils.sqs_helper.write_message_json")
    def test_no_notify(self, mock_write_message):
        all_fields = set(core.models.settings.AdGroupSettings._settings_fields)
        no_notify_fields = all_fields - self.notify_fields

        for field in no_notify_fields:
            update_notifier.notify_ad_group_settings_change(self.ad_group.settings, {field: "New value"})
            self.assertFalse(mock_write_message.called)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    @patch("automation.campaignstop.service.update_handler.handle_updates.delay")
    @patch("automation.campaignstop.service.update_notifier._time", return_value=12345)
    def test_notify(self, mock_time, mock_handle_updates):
        for field in self.notify_fields:
            mock_handle_updates.reset_mock()
            update_notifier.notify_ad_group_settings_change(self.ad_group.settings, {"state": 1})
            mock_handle_updates.assert_called_with(
                self.ad_group.campaign_id, constants.CampaignUpdateType.DAILY_CAP, 12345
            )


class AdGroupSourceSettingsNotifyTest(TestCase):
    def setUp(self):
        self.ad_group_source = magic_mixer.blend(
            core.models.AdGroupSource, ad_group__campaign__real_time_campaign_stop=True
        )
        self.notify_fields = set(update_notifier.AD_GROUP_SOURCE_SETTINGS_FIELDS)

    @patch("utils.sqs_helper.write_message_json")
    def test_no_notify(self, mock_write_message):
        all_fields = set(core.models.settings.AdGroupSourceSettings._settings_fields)
        no_notify_fields = all_fields - self.notify_fields
        for field in no_notify_fields:
            update_notifier.notify_ad_group_source_settings_change(self.ad_group_source.settings, {field: "New value"})
            self.assertFalse(mock_write_message.called)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    @patch("automation.campaignstop.service.update_handler.handle_updates.delay")
    @patch("automation.campaignstop.service.update_notifier._time", return_value=12345)
    def test_notify(self, mock_time, mock_handle_updates):
        for field in self.notify_fields:
            mock_handle_updates.reset_mock()

            update_notifier.notify_ad_group_source_settings_change(self.ad_group_source.settings, {field: "New value"})
            mock_handle_updates.assert_called_with(
                self.ad_group_source.ad_group.campaign_id, constants.CampaignUpdateType.DAILY_CAP, 12345
            )


class BudgetLineItemNotifyTest(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(core.models.Campaign, real_time_campaign_stop=True)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    @patch("automation.campaignstop.service.update_handler.handle_updates.delay")
    @patch("automation.campaignstop.service.update_notifier._time", return_value=12345)
    def test_notify(self, mock_time, mock_handle_updates):
        update_notifier.notify_budget_line_item_change(self.campaign)
        mock_handle_updates.assert_called_with(self.campaign.id, constants.CampaignUpdateType.BUDGET, 12345)
