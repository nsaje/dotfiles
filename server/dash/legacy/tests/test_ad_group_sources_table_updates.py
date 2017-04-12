from django.test import TestCase

from dash.legacy import ad_group_source_table_updates
from dash import models
from dash import table
from dash.views import helpers
from zemauth.models import User
from decimal import Decimal
from datetime import datetime


class AdGroupSourcesTableUpdatesTest(TestCase):

    fixtures = ['test_api_breakdowns']

    def test_get(self):
        response = table.AdGroupSourcesTableUpdates().get(User.objects.get(pk=1), None, None, 1)
        expected = {
            'notifications': {},
            'in_progress': False,
            'rows': {
                1: {
                    'status': 1,
                    'status_setting': 1,
                    'current_daily_budget': Decimal('10.0000'),
                    'daily_budget': Decimal('10.0000'),
                    'bid_cpc': Decimal('0.5010'),
                    'current_bid_cpc': Decimal('0.5010')
                },
                2: {
                    'status': 2,
                    'status_setting': 2,
                    'current_daily_budget': Decimal('20.0000'),
                    'daily_budget': Decimal('20.0000'),
                    'bid_cpc': Decimal('0.5020'),
                    'current_bid_cpc': Decimal('0.5020')
                }
            },
            'last_change': datetime(2014, 6, 5, 9, 58, 21),
            'totals': {
                'current_daily_budget': Decimal('10.0000'),
                'daily_budget': Decimal('10.0000')
            }
        }
        self.assertDictEqual(expected, response)

    def test_update_rtb_source_row_disabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        row = {
            'status': 2,
            'status_setting': 2,
            'current_daily_budget': Decimal('20.0000'),
            'daily_budget': Decimal('20.0000'),
            'bid_cpc': Decimal('0.5020'),
            'current_bid_cpc': Decimal('0.5020')
        }
        expected = {
            'status': 2,
            'status_setting': 2,
            'current_daily_budget': Decimal('20.0000'),
            'daily_budget': Decimal('20.0000'),
            'bid_cpc': Decimal('0.5020'),
            'current_bid_cpc': Decimal('0.5020')
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
            'status': 1,
            'status_setting': 1,
            'current_daily_budget': Decimal('20.0000'),
            'daily_budget': Decimal('20.0000'),
            'bid_cpc': Decimal('0.5020'),
            'current_bid_cpc': Decimal('0.5020')
        }
        expected = {
            'status': 1,
            'status_setting': 1,
            'bid_cpc': Decimal('0.5020'),
            'current_bid_cpc': Decimal('0.5020')
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
            'status': 1,
            'status_setting': 1,
            'current_daily_budget': Decimal('20.0000'),
            'daily_budget': Decimal('20.0000'),
            'bid_cpc': Decimal('0.5020'),
            'current_bid_cpc': Decimal('0.5020')
        }
        expected = {
            'status': 2,
            'status_setting': 1,
            'bid_cpc': Decimal('0.5020'),
            'current_bid_cpc': Decimal('0.5020')
        }

        notifications = {}
        rows = {ad_group_source.source_id: row}
        ad_group_source_table_updates._update_rtb_source_row(ad_group_settings, ad_group_source, rows, notifications)
        self.assertDictEqual(expected, row)

    def test_get_daily_budget(self):
        ad_group = models.AdGroup.objects.get(id=1)
        ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
        ad_group_settings = ad_group.get_current_settings()
        ad_group_sources_states = helpers.get_ad_group_sources_states(ad_group_sources)

        self.assertEqual(Decimal('10.0'), ad_group_source_table_updates._get_daily_budget(ad_group_settings, ad_group_sources_states))

    def test_get_daily_budget_all_rtb_enabled(self):
        ad_group = models.AdGroup.objects.get(id=1)
        ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
        ad_group_settings = ad_group.get_current_settings()
        ad_group_sources_states = helpers.get_ad_group_sources_states(ad_group_sources)

        ad_group_settings.b1_sources_group_enabled = True
        ad_group_settings.b1_sources_group_state = 1
        ad_group_settings.b1_sources_group_daily_budget = Decimal(100)

        self.assertEqual(Decimal('100.0'), ad_group_source_table_updates._get_daily_budget(ad_group_settings, ad_group_sources_states))

    def test_get_daily_budget_all_rtb_enabled_and_inactive(self):
        ad_group = models.AdGroup.objects.get(id=1)
        ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
        ad_group_settings = ad_group.get_current_settings()
        ad_group_sources_states = helpers.get_ad_group_sources_states(ad_group_sources)
        ad_group_settings.b1_sources_group_enabled = True
        ad_group_settings.b1_sources_group_state = 2
        ad_group_settings.b1_sources_group_daily_budget = Decimal(100)

        self.assertEqual(Decimal('0.0'), ad_group_source_table_updates._get_daily_budget(ad_group_settings, ad_group_sources_states))
