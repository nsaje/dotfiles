from datetime import datetime
from decimal import Decimal

from django.test import TestCase

from dash import constants
from dash import models
from dash.legacy import ad_group_source_table_updates
from dash.views import helpers
from zemauth.models import User


class AdGroupSourcesTableUpdatesTest(TestCase):

    fixtures = ["test_api_breakdowns"]

    def test_get(self):
        response = ad_group_source_table_updates.get_updated_ad_group_sources_changes(
            User.objects.get(pk=1), None, None, 1
        )

        expected = {
            "notifications": {},
            "in_progress": False,
            "rows": {
                1: {
                    "status": 1,
                    "status_setting": 1,
                    "current_daily_budget": Decimal("10.0000"),
                    "daily_budget": Decimal("10.0000"),
                    "bid_cpc": Decimal("0.5010"),
                    "current_bid_cpc": Decimal("0.5010"),
                    "bid_cpm": Decimal("0.4010"),
                    "current_bid_cpm": Decimal("0.4010"),
                },
                2: {
                    "status": 2,
                    "status_setting": 2,
                    "current_daily_budget": Decimal("20.0000"),
                    "daily_budget": Decimal("20.0000"),
                    "bid_cpc": Decimal("0.5020"),
                    "current_bid_cpc": Decimal("0.5020"),
                    "bid_cpm": Decimal("0.4020"),
                    "current_bid_cpm": Decimal("0.4020"),
                },
            },
            "last_change": datetime(2014, 6, 5, 9, 58, 21),
            "totals": {"current_daily_budget": Decimal("10.0000"), "daily_budget": Decimal("10.0000")},
        }
        self.assertDictEqual(expected, response)

    def test_get_all_rtb_enabled(self):
        models.AdGroup.objects.get(pk=1).settings.update_unsafe(
            None,
            b1_sources_group_enabled=True,
            b1_sources_group_state=constants.AdGroupSourceSettingsState.ACTIVE,
            local_b1_sources_group_cpc_cc=Decimal("0.01"),
            local_b1_sources_group_cpm=Decimal("1.01"),
            b1_sources_group_daily_budget=Decimal("5.0"),
            local_b1_sources_group_daily_budget=Decimal("10.0"),
        )
        response = ad_group_source_table_updates.get_updated_ad_group_sources_changes(
            User.objects.get(pk=1), None, None, 1
        )
        expected = {
            "notifications": {},
            "in_progress": False,
            "rows": {
                1: {
                    "status": 1,
                    "status_setting": 1,
                    "bid_cpc": Decimal("0.5010"),
                    "current_bid_cpc": Decimal("0.5010"),
                    "bid_cpm": Decimal("0.4010"),
                    "current_bid_cpm": Decimal("0.4010"),
                },
                2: {
                    "status": 2,
                    "status_setting": 2,
                    "current_daily_budget": Decimal("20.0000"),
                    "daily_budget": Decimal("20.0000"),
                    "bid_cpc": Decimal("0.5020"),
                    "current_bid_cpc": Decimal("0.5020"),
                    "bid_cpm": Decimal("0.4020"),
                    "current_bid_cpm": Decimal("0.4020"),
                },
                "0123456789": {
                    "status": 1,
                    "status_setting": 1,
                    "current_daily_budget": Decimal("10.0000"),
                    "daily_budget": Decimal("10.0000"),
                    "bid_cpc": Decimal("0.0100"),
                    "current_bid_cpc": Decimal("0.0100"),
                    "bid_cpm": Decimal("1.0100"),
                    "current_bid_cpm": Decimal("1.0100"),
                },
            },
            "last_change": datetime(2014, 6, 5, 9, 58, 21),
            "totals": {"current_daily_budget": Decimal("10.0000"), "daily_budget": Decimal("10.0000")},
        }
        self.assertDictEqual(expected, response)

    def test_update_rtb_source_row_disabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        row = {
            "status": 2,
            "status_setting": 2,
            "current_daily_budget": Decimal("20.0000"),
            "daily_budget": Decimal("20.0000"),
            "bid_cpc": Decimal("0.5020"),
            "current_bid_cpc": Decimal("0.5020"),
            "bid_cpm": Decimal("0.4020"),
            "current_bid_cpm": Decimal("0.4020"),
        }
        expected = {
            "status": 2,
            "status_setting": 2,
            "current_daily_budget": Decimal("20.0000"),
            "daily_budget": Decimal("20.0000"),
            "bid_cpc": Decimal("0.5020"),
            "current_bid_cpc": Decimal("0.5020"),
            "bid_cpm": Decimal("0.4020"),
            "current_bid_cpm": Decimal("0.4020"),
        }

        notifications = {}
        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        rows = {ad_group_source.source_id: row}
        ad_group_source_table_updates._update_rtb_source_row(ad_group_settings, ad_group_source, rows, notifications)
        self.assertDictEqual(expected, row)

    def test_update_rtb_source_row_enabled_inactive(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.b1_sources_group_enabled = True
        ad_group_settings.b1_sources_group_state = 1

        row = {
            "status": 1,
            "status_setting": 1,
            "current_daily_budget": Decimal("20.0000"),
            "daily_budget": Decimal("20.0000"),
            "bid_cpc": Decimal("0.5020"),
            "current_bid_cpc": Decimal("0.5020"),
            "bid_cpm": Decimal("0.4020"),
            "current_bid_cpm": Decimal("0.4020"),
        }
        expected = {
            "status": 1,
            "status_setting": 1,
            "bid_cpc": Decimal("0.5020"),
            "current_bid_cpc": Decimal("0.5020"),
            "bid_cpm": Decimal("0.4020"),
            "current_bid_cpm": Decimal("0.4020"),
        }

        notifications = {}
        rows = {ad_group_source.source_id: row}
        ad_group_source_table_updates._update_rtb_source_row(ad_group_settings, ad_group_source, rows, notifications)
        self.assertDictEqual(expected, row)

    def test_update_rtb_source_row_enabled_and_inactive(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.b1_sources_group_enabled = True
        ad_group_settings.b1_sources_group_state = 2

        row = {
            "status": 1,
            "status_setting": 1,
            "current_daily_budget": Decimal("20.0000"),
            "daily_budget": Decimal("20.0000"),
            "bid_cpc": Decimal("0.5020"),
            "current_bid_cpc": Decimal("0.5020"),
            "bid_cpm": Decimal("0.4020"),
            "current_bid_cpm": Decimal("0.4020"),
        }
        expected = {
            "status": 2,
            "status_setting": 1,
            "bid_cpc": Decimal("0.5020"),
            "current_bid_cpc": Decimal("0.5020"),
            "bid_cpm": Decimal("0.4020"),
            "current_bid_cpm": Decimal("0.4020"),
        }

        notifications = {}
        rows = {ad_group_source.source_id: row}
        ad_group_source_table_updates._update_rtb_source_row(ad_group_settings, ad_group_source, rows, notifications)
        self.assertDictEqual(expected, row)

    def test_get_daily_budget(self):
        ad_group = models.AdGroup.objects.get(id=1)
        ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
        ad_group_settings = ad_group.get_current_settings()
        ad_group_sources_settings = helpers.get_ad_group_sources_settings(ad_group_sources)

        self.assertEqual(
            Decimal("10.0"),
            ad_group_source_table_updates._get_daily_budget(
                User.objects.get(pk=1), [], ad_group_settings, ad_group_sources_settings
            ),
        )

    def test_get_daily_budget_filtered_sources(self):
        ad_group = models.AdGroup.objects.get(id=2)
        ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
        ad_group_settings = ad_group.get_current_settings()
        ad_group_sources_settings = helpers.get_ad_group_sources_settings(ad_group_sources)

        filtered_sources = [2]

        self.assertEqual(
            Decimal("40.0"),
            ad_group_source_table_updates._get_daily_budget(
                User.objects.get(pk=1), filtered_sources, ad_group_settings, ad_group_sources_settings
            ),
        )

    def test_get_daily_budget_all_rtb_enabled(self):
        ad_group = models.AdGroup.objects.get(id=1)
        ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
        ad_group_settings = ad_group.get_current_settings()
        ad_group_sources_settings = helpers.get_ad_group_sources_settings(ad_group_sources)

        ad_group_settings.b1_sources_group_enabled = True
        ad_group_settings.b1_sources_group_state = 1
        ad_group_settings.b1_sources_group_daily_budget = Decimal(100)
        ad_group_settings.local_b1_sources_group_daily_budget = Decimal(200)

        self.assertEqual(
            Decimal("200.0"),
            ad_group_source_table_updates._get_daily_budget(
                User.objects.get(pk=1), [], ad_group_settings, ad_group_sources_settings
            ),
        )

    def test_get_daily_budget_all_rtb_enabled_and_inactive(self):
        ad_group = models.AdGroup.objects.get(id=1)
        ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
        ad_group_settings = ad_group.get_current_settings()
        ad_group_sources_settings = helpers.get_ad_group_sources_settings(ad_group_sources)
        ad_group_settings.b1_sources_group_enabled = True
        ad_group_settings.b1_sources_group_state = 2
        ad_group_settings.b1_sources_group_daily_budget = Decimal(100)

        self.assertEqual(
            Decimal("0.0"),
            ad_group_source_table_updates._get_daily_budget(
                User.objects.get(pk=1), [], ad_group_settings, ad_group_sources_settings
            ),
        )
