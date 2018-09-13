import datetime
from unittest.mock import patch

import django.test

import dash.constants
import dash.models
from utils.magic_mixer import magic_mixer

from . import constants
from . import models
from . import service


class YahooFinalizeMigrationTestCase(django.test.TestCase):
    @classmethod
    def setUpClass(cls):
        super(YahooFinalizeMigrationTestCase, cls).setUpClass()
        yahoo_account = magic_mixer.blend(dash.models.YahooAccount, advertiser_id="AID")
        cls.account = magic_mixer.blend(dash.models.Account, yahoo_account=yahoo_account)
        cls.other_account = magic_mixer.blend(dash.models.Account)
        source_type = magic_mixer.blend(dash.models.SourceType, type=dash.constants.SourceType.YAHOO)
        cls.source_yahoo = magic_mixer.blend(dash.models.Source, source_type=source_type)
        cls.source_other = magic_mixer.blend(dash.models.Source)

    @patch.object(service, "update_source_content_ad_ids")
    @patch.object(service, "update_source_campaign_keys")
    @patch.object(service, "update_yahoo_account")
    @patch("utils.dates_helper.local_today")
    @patch("utils.k1_helper")
    def test_finalize_migration(
        self, mock_k1_helper, mock_today, mock_update_account, mock_update_ad_group, mock_update_content_ad
    ):
        mock_today.return_value = datetime.date(2018, 5, 10)
        mock_k1_helper.get_yahoo_migration.return_value = {
            "status": constants.MIGRATION_STATUS_SWITCHOVER,
            "switchover_date": "2018-05-05",
            "currency": dash.constants.Currency.USD,
            "advertiser_id": "ID",
        }

        service.finalize_migration(self.account.id)

        mock_k1_helper.get_yahoo_migration.assert_called_once_with(self.account.id)
        mock_k1_helper.get_yahoo_migration_campaign_mappings.assert_called_once_with(self.account.id)
        mock_k1_helper.get_yahoo_migration_content_ad_mappings.assert_called_once_with(self.account.id)
        mock_k1_helper.update_yahoo_migration.assert_called_once_with(
            self.account.id, status=constants.MIGRATION_STATUS_FINISHED
        )
        mock_update_account.assert_called_once_with(self.account, mock_k1_helper.get_yahoo_migration.return_value)
        mock_update_ad_group.assert_called_once_with(self.account, {})
        mock_update_content_ad.assert_called_once_with(self.account, {})

    @patch("utils.k1_helper")
    def test_finalize_migration_no_migration(self, mock_k1_helper):
        mock_k1_helper.get_yahoo_migration.return_value = None
        with self.assertRaises(service.CannotRunMigrationException):
            service.finalize_migration(self.account.id)

    @patch("utils.k1_helper")
    def test_finalize_migration_wrong_status(self, mock_k1_helper):
        mock_k1_helper.get_yahoo_migration.return_value = {"status": constants.MIGRATION_STATUS_SYNCING_TO_BOTH}
        with self.assertRaises(service.CannotRunMigrationException):
            service.finalize_migration(self.account.id)

    @patch("utils.dates_helper.local_today")
    @patch("utils.k1_helper")
    def test_finalize_migration_before_switchover(self, mock_k1_helper, mock_today):
        mock_today.return_value = datetime.date(2018, 5, 10)
        mock_k1_helper.get_yahoo_migration.return_value = {
            "status": constants.MIGRATION_STATUS_SWITCHOVER,
            "switchover_date": "2018-05-11",
        }
        with self.assertRaises(service.CannotRunMigrationException):
            service.finalize_migration(self.account.id)

    def test_update_yahoo_account(self):
        data = {"advertiser_id": "12345", "currency": dash.constants.Currency.USD}

        service.update_yahoo_account(self.account, data)

        self.account.refresh_from_db()
        self.assertEqual(self.account.yahoo_account.advertiser_id, data["advertiser_id"])

    def test_update_source_campaign_keys(self):
        yahoo_ad_group_sources = magic_mixer.cycle(2).blend(
            dash.models.AdGroupSource,
            ad_group__campaign__account=self.account,
            source=self.source_yahoo,
            source_campaign_key="test-old",
        )
        other_ad_group_source = magic_mixer.blend(
            dash.models.AdGroupSource,
            ad_group__campaign__account=self.account,
            source=self.source_other,
            source_campaign_key="test-old",
        )
        other_account_ad_group_source = magic_mixer.blend(
            dash.models.AdGroupSource,
            ad_group__campaign__account=self.other_account,
            source=self.source_yahoo,
            source_campaign_key="test-old",
        )

        mapping = {yahoo_ad_group_sources[0].ad_group_id: "test-new"}

        service.update_source_campaign_keys(self.account, mapping)

        yahoo_ad_group_sources[0].refresh_from_db()
        self.assertEqual(yahoo_ad_group_sources[0].source_campaign_key, "test-new")
        yahoo_ad_group_sources[1].refresh_from_db()
        self.assertEqual(yahoo_ad_group_sources[1].source_campaign_key, {})
        other_ad_group_source.refresh_from_db()
        self.assertEqual(other_ad_group_source.source_campaign_key, "test-old")
        other_account_ad_group_source.refresh_from_db()
        self.assertEqual(other_account_ad_group_source.source_campaign_key, "test-old")

        self.assertEqual(models.YahooMigrationAdGroupHistory.objects.count(), 2)
        self.assertEqual(
            models.YahooMigrationAdGroupHistory.objects.get(
                ad_group=yahoo_ad_group_sources[0].ad_group
            ).source_campaign_key,
            "test-old",
        )
        self.assertEqual(
            models.YahooMigrationAdGroupHistory.objects.get(
                ad_group=yahoo_ad_group_sources[1].ad_group
            ).source_campaign_key,
            "test-old",
        )

    def test_update_source_content_ad_ids(self):
        yahoo_content_ad_sources = magic_mixer.cycle(2).blend(
            dash.models.ContentAdSource,
            content_ad__tracker_urls=[],
            content_ad__ad_group__campaign__account=self.account,
            source=self.source_yahoo,
            source_content_ad_id="test-old",
        )
        other_content_ad_source = magic_mixer.blend(
            dash.models.ContentAdSource,
            content_ad__tracker_urls=[],
            content_ad__ad_group__campaign__account=self.account,
            source=self.source_other,
            source_content_ad_id="test-old",
        )
        other_account_content_ad_source = magic_mixer.blend(
            dash.models.ContentAdSource,
            content_ad__tracker_urls=[],
            content_ad__ad_group__campaign__account=self.other_account,
            source=self.source_yahoo,
            source_content_ad_id="test-old",
        )

        mapping = {yahoo_content_ad_sources[0].content_ad_id: "test-new"}

        service.update_source_content_ad_ids(self.account, mapping)

        yahoo_content_ad_sources[0].refresh_from_db()
        self.assertEqual(yahoo_content_ad_sources[0].source_content_ad_id, "test-new")
        yahoo_content_ad_sources[1].refresh_from_db()
        self.assertEqual(yahoo_content_ad_sources[1].source_content_ad_id, None)
        other_content_ad_source.refresh_from_db()
        self.assertEqual(other_content_ad_source.source_content_ad_id, "test-old")
        other_account_content_ad_source.refresh_from_db()
        self.assertEqual(other_account_content_ad_source.source_content_ad_id, "test-old")

        self.assertEqual(models.YahooMigrationContentAdHistory.objects.count(), 2)
        self.assertEqual(
            models.YahooMigrationContentAdHistory.objects.get(
                content_ad=yahoo_content_ad_sources[0].content_ad
            ).source_content_ad_id,
            "test-old",
        )
        self.assertEqual(
            models.YahooMigrationContentAdHistory.objects.get(
                content_ad=yahoo_content_ad_sources[1].content_ad
            ).source_content_ad_id,
            "test-old",
        )
