import datetime

import mock
from django.test import TestCase

from dash import constants
from dash import models
from dash.management.commands import auto_archive_inactive_entities
from utils import dates_helper
from utils.magic_mixer import magic_mixer


@mock.patch("redshiftapi.api_breakdowns.query", return_value={})
@mock.patch("core.models.ad_group.instance.AdGroupInstanceMixin.write_history")
@mock.patch("core.models.campaign.instance.CampaignInstanceMixin.write_history")
class AutoArchiveTest(TestCase):
    def setUp(self):
        self.inactive_since = dates_helper.local_today() - datetime.timedelta(
            days=auto_archive_inactive_entities.DAYS_INACTIVE
        )
        self.time_delta = datetime.timedelta(days=1)

    def test_active(self, campaign_history_mock, ad_group_history_mock, spend_mock):
        campaign = magic_mixer.blend(models.Campaign)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since + self.time_delta, archived=False)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None,
            created_dt=self.inactive_since + self.time_delta,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since
        )
        campaign.refresh_from_db()
        campaign.settings.refresh_from_db()
        ad_group.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 0)

    def test_inactive_adgroup(self, campaign_history_mock, ad_group_history_mock, spend_mock):
        campaign = magic_mixer.blend(models.Campaign)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since + self.time_delta, archived=False)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None, created_dt=self.inactive_since, archived=False, state=constants.AdGroupSettingsState.INACTIVE
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since
        )
        campaign.refresh_from_db()
        campaign.settings.refresh_from_db()
        ad_group.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 1)
        ad_group_history_mock.assert_called_with(changes_text="Automated archiving.")

    def test_inactive_campaign(self, campaign_history_mock, ad_group_history_mock, spend_mock):
        campaign = magic_mixer.blend(models.Campaign)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since, archived=False)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None,
            created_dt=self.inactive_since,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            end_date=self.inactive_since,
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since
        )
        campaign.refresh_from_db()
        campaign.settings.refresh_from_db()
        ad_group.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertTrue(campaign.archived)
        self.assertTrue(campaign.settings.archived)
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(campaign_count, 1)
        self.assertEqual(adgroup_count, 1)
        campaign_history_mock.assert_called_with(changes_text="Automated archiving.")
        ad_group_history_mock.assert_called_with(changes_text="Automated archiving.")

    def test_active_adgroup(self, campaign_history_mock, ad_group_history_mock, spend_mock):
        campaign = magic_mixer.blend(models.Campaign)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since, archived=False)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None,
            created_dt=self.inactive_since + self.time_delta,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since
        )
        campaign.refresh_from_db()
        campaign.settings.refresh_from_db()
        ad_group.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 0)

    def test_mixed_adgroups(self, campaign_history_mock, ad_group_history_mock, spend_mock):
        campaign = magic_mixer.blend(models.Campaign)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since, archived=False)
        ad_group_new = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group_new.settings.update_unsafe(
            None,
            created_dt=self.inactive_since + self.time_delta,
            archived=False,
            state=constants.AdGroupSettingsState.INACTIVE,
        )
        ad_group_old = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group_old.settings.update_unsafe(
            None, created_dt=self.inactive_since, archived=False, state=constants.AdGroupSettingsState.INACTIVE
        )
        ad_group_active = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group_active.settings.update_unsafe(
            None,
            created_dt=self.inactive_since + self.time_delta,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            end_date=self.inactive_since,
        )
        ad_group_old_active = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group_old_active.settings.update_unsafe(
            None,
            created_dt=self.inactive_since,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            end_date=self.inactive_since,
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since
        )
        campaign.refresh_from_db()
        campaign.settings.refresh_from_db()
        ad_group_new.refresh_from_db()
        ad_group_new.settings.refresh_from_db()
        ad_group_old.refresh_from_db()
        ad_group_old.settings.refresh_from_db()
        ad_group_active.refresh_from_db()
        ad_group_active.settings.refresh_from_db()
        ad_group_old_active.refresh_from_db()
        ad_group_old_active.settings.refresh_from_db()
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
        self.assertFalse(ad_group_new.archived)
        self.assertFalse(ad_group_new.settings.archived)
        self.assertTrue(ad_group_old.archived)
        self.assertTrue(ad_group_old.settings.archived)
        self.assertFalse(ad_group_active.archived)
        self.assertFalse(ad_group_active.settings.archived)
        self.assertTrue(ad_group_old_active.archived)
        self.assertTrue(ad_group_old_active.settings.archived)
        self.assertEqual(ad_group_new.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(ad_group_old.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(ad_group_active.settings.state, constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(ad_group_old_active.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 2)
        ad_group_history_mock.assert_called_with(changes_text="Automated archiving.")

    def test_auto_archiving_disabled(self, campaign_history_mock, ad_group_history_mock, spend_mock):
        account = magic_mixer.blend(models.Account, auto_archiving_enabled=False)
        campaign = magic_mixer.blend(models.Campaign, account=account)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since, archived=False)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None,
            created_dt=self.inactive_since,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            end_date=self.inactive_since,
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since
        )
        campaign.refresh_from_db()
        campaign.settings.refresh_from_db()
        ad_group.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 0)

    def test_auto_archiving_active_budget(self, campaign_history_mock, ad_group_history_mock, spend_mock):
        account = magic_mixer.blend(models.Account, auto_archiving_enabled=True)
        campaign = magic_mixer.blend(models.Campaign, account=account)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since, archived=False)
        credit = magic_mixer.blend(
            models.CreditLineItem,
            account=account,
            status=constants.CreditLineItemStatus.SIGNED,
            start_date=self.inactive_since,
            end_date=dates_helper.local_today,
            amount=1000,
        )
        magic_mixer.blend(
            models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=self.inactive_since,
            end_date=dates_helper.local_today,
            amount=100,
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since
        )
        campaign.refresh_from_db()
        campaign.settings.refresh_from_db()
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 0)

    def test_whitelist_included(self, campaign_history_mock, ad_group_history_mock, spend_mock):
        account = magic_mixer.blend(models.Account)
        campaign = magic_mixer.blend(models.Campaign, account=account)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since, archived=False)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None,
            created_dt=self.inactive_since,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            end_date=self.inactive_since,
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since, whitelist=[account.id]
        )
        campaign.refresh_from_db()
        campaign.settings.refresh_from_db()
        ad_group.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertTrue(campaign.archived)
        self.assertTrue(campaign.settings.archived)
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(campaign_count, 1)
        self.assertEqual(adgroup_count, 1)
        campaign_history_mock.assert_called_with(changes_text="Automated archiving.")
        ad_group_history_mock.assert_called_with(changes_text="Automated archiving.")

    def test_whitelist_not_included(self, campaign_history_mock, ad_group_history_mock, spend_mock):
        account = magic_mixer.blend(models.Account)
        campaign = magic_mixer.blend(models.Campaign, account=account)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since, archived=False)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None,
            created_dt=self.inactive_since,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            end_date=self.inactive_since,
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since, whitelist=[account.id + 1]
        )
        campaign.refresh_from_db()
        campaign.settings.refresh_from_db()
        ad_group.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 0)
