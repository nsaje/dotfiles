import mock
import datetime

from dash import models
from dash import constants

from django.test import TestCase
from utils.magic_mixer import magic_mixer
from utils import dates_helper

from dash.management.commands import auto_archive_inactive_entities


@mock.patch("redshiftapi.api_breakdowns.query", return_value={})
class AutoArchiveTest(TestCase):
    def setUp(self):
        self.inactive_since = dates_helper.local_today() - datetime.timedelta(
            days=auto_archive_inactive_entities.DAYS_INACTIVE
        )
        self.time_delta = datetime.timedelta(days=1)

    def test_active(self, spend_mock):
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
        campaign.settings.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertFalse(campaign.settings.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 0)

    def test_inactive_adgroup(self, spend_mock):
        campaign = magic_mixer.blend(models.Campaign)
        campaign.settings.update_unsafe(None, created_dt=self.inactive_since + self.time_delta, archived=False)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None, created_dt=self.inactive_since, archived=False, state=constants.AdGroupSettingsState.INACTIVE
        )
        adgroup_count, campaign_count = auto_archive_inactive_entities._auto_archive_inactive_entities(
            self.inactive_since
        )
        campaign.settings.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertFalse(campaign.settings.archived)
        self.assertTrue(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 1)

    def test_inactive_campaign(self, spend_mock):
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
        campaign.settings.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertTrue(campaign.settings.archived)
        self.assertTrue(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(campaign_count, 1)
        self.assertEqual(adgroup_count, 1)

    def test_active_adgroup(self, spend_mock):
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
        campaign.settings.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertFalse(campaign.settings.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 0)

    def test_mixed_adgroups(self, spend_mock):
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
        campaign.settings.refresh_from_db()
        ad_group_new.settings.refresh_from_db()
        ad_group_old.settings.refresh_from_db()
        ad_group_active.settings.refresh_from_db()
        ad_group_old_active.settings.refresh_from_db()
        self.assertFalse(campaign.settings.archived)
        self.assertFalse(ad_group_new.settings.archived)
        self.assertTrue(ad_group_old.settings.archived)
        self.assertFalse(ad_group_active.settings.archived)
        self.assertTrue(ad_group_old_active.settings.archived)
        self.assertEqual(ad_group_new.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(ad_group_old.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(ad_group_active.settings.state, constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(ad_group_old_active.settings.state, constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 2)

    def test_auto_archiving_disabled(self, spend_mock):
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
        campaign.settings.refresh_from_db()
        ad_group.settings.refresh_from_db()
        self.assertFalse(campaign.settings.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(ad_group.settings.state, constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 0)

    def test_auto_archiving_active_budget(self, spend_mock):
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
        campaign.settings.refresh_from_db()
        self.assertFalse(campaign.settings.archived)
        self.assertEqual(campaign_count, 0)
        self.assertEqual(adgroup_count, 0)
