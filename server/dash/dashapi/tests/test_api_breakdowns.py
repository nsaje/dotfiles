import datetime
from decimal import Decimal
from mock import patch

from django.test import TestCase, override_settings

from utils.dict_helper import dict_join
from zemauth.models import User

from dash import models
from dash import threads
from dash.constants import Level
from dash.dashapi import api_breakdowns
from dash.dashapi import helpers
from dash.dashapi import augmenter


START_DATE, END_DATE = datetime.date(2016, 7, 1), datetime.date(2016, 8, 31)
EMPTY_ACCOUNT_PROJECTIONS = {
    'pacing': None,
    'allocated_budgets': Decimal('0'),
    'spend_projection': Decimal('0'),
    'license_fee_projection': Decimal('0'),
    'flat_fee': 0,
    'total_fee': 0,
    'total_fee_projection': Decimal('0'),
}

EMPTY_CAMPAIGN_PROJECTIONS = {
    'pacing': None,
    'allocated_budgets': None,
    'spend_projection': None,
    'license_fee_projection': None,
}


@patch('dash.threads.AsyncFunction', threads.MockAsyncFunction)
@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_all_accounts_break_account(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 1
        )

        self.assertEqual(rows, [
            dict_join({'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_query_all_accounts_break_source(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_all_accounts_break_account_source(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'account_id': 1}],
            'name', 0, 2
        )

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_all_accounts_break_source_account(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 1
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1, 'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
            dict_join({'source_id': 2, 'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_query_all_accounts_break_source_campaign(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 1
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'source_id': 2, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_all_accounts_break_account_campaign(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'account_id': 1}, {'account_id': 2}],
            'name', 0, 1
        )

        self.assertEqual(rows, [
            dict_join({'account_id': 1, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_accounts_break_campaign(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            dict_join({'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'campaign_id': 2, 'archived': True, 'name': 'test campaign 2', 'status': 2},
                      {'campaign_manager': 'mad.max@zemanta.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_accounts_break_source(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_accounts_break_campaign_source(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id', 'source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'campaign_id': 1}, {'campaign_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [{
            'archived': False, 'name': 'AdsNative', 'campaign_id': 1, 'maintenance': False, 'source_id': 1, 'id': 1,
        }, {
            'archived': False, 'name': 'Gravity', 'campaign_id': 1, 'maintenance': False, 'source_id': 2, 'id': 2,
        }, {
            'archived': False, 'name': 'AdsNative', 'campaign_id': 2, 'maintenance': False, 'source_id': 1, 'id': 1,
        }])

    def test_query_accounts_break_source_campaign(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            dict_join({'source_id': 1, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'source_id': 1, 'campaign_id': 2, 'archived': True, 'name': 'test campaign 2', 'status': 2},
                      {'campaign_manager': 'mad.max@zemanta.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'source_id': 2, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_accounts_break_source_ad_group(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'ad_group_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'source_id': 1, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1},
            {'source_id': 1, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2},
            {'source_id': 2, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1},
            {'source_id': 2, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2},
        ])

    def test_query_accounts_break_campaign_ad_group_not_allowed(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id', 'ad_group_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'campaign_id': 1}, {'campaign_id': 2}],  # campaign 2 is not allowed
            'name', 0, 2
        )

        # campaign_id: 2 does not get queried
        self.assertEqual(rows, [
            {'campaign_id': 1, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1},
            {'campaign_id': 1, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2},
        ])

    def test_query_accounts_break_campaign_ad_group(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id', 'ad_group_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'campaign_id': 1}],
            'name', 0, 2
        )

        self.assertEqual(rows, [
            {'campaign_id': 1, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1},
            {'campaign_id': 1, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2},
        ])

    def test_query_campaigns_break_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1,
             'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2,
             'campaign_has_available_budget': False, 'campaign_stop_inactive': False},
        ])

    def test_query_campaigns_break_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_campaigns_break_ad_group_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id', 'source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group__campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'ad_group_id': 1}, {'ad_group_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'ad_group_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_campaigns_break_source_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id', 'ad_group_id'],
            {
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'campaign': models.Campaign.objects.get(pk=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}, {'source_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'source_id': 1, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1},
            {'source_id': 1, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2},
            {'source_id': 2, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1},
            {'source_id': 2, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2},
        ])

    def test_query_ad_groups_break_content_ad(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['content_ad_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {
                'image_hash': '100',
                'description': 'Example description',
                'content_ad_id': 1,
                'redirector_url': 'http://r1.zemanta.com/b/r1/z1/1/1/',
                'brand_name': 'Example',
                'image_urls': {
                    'square': '/100.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                    'landscape': '/100.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
                },
                'batch_name': 'batch 1',
                'archived': False,
                'name': 'Title 1',
                'display_url': 'example.com',
                'url': 'http://testurl1.com',
                'call_to_action': 'Call to action',
                'label': '',
                'state': 1,
                'status': 1,
                'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
                'batch_id': 1,
                'title': 'Title 1',
                'status_per_source': {
                    1: {
                        'source_id': 1,
                        'submission_status': 1,
                        'source_name': 'AdsNative',
                        'source_status': 1,
                        'submission_errors': None
                    },
                    2: {
                        'source_id': 2,
                        'submission_status': 2,
                        'source_name': 'Gravity',
                        'source_status': 2,
                        'submission_errors': None
                    }
                },
            }, {
                'image_hash': '200',
                'description': 'Example description',
                'content_ad_id': 2,
                'redirector_url': 'http://r1.zemanta.com/b/r2/z1/1/2/',
                'brand_name': 'Example',
                'image_urls': {
                    'square': '/200.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                    'landscape': '/200.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
                },
                'batch_name': 'batch 1',
                'archived': False,
                'name': 'Title 2',
                'display_url': 'example.com',
                'url': 'http://testurl2.com',
                'call_to_action': 'Call to action',
                'label': '',
                'state': 2,
                'status': 2,
                'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
                'batch_id': 1,
                'title': 'Title 2',
                'status_per_source': {
                    2: {
                        'source_id': 2,
                        'submission_status': 2,
                        'source_name': 'Gravity',
                        'source_status': 2,
                        'submission_errors': None
                    }
                },
            },
        ])

    def test_query_ad_groups_break_content_ad_source(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['content_ad_id', 'source_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'content_ad_id': 1}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [{
            'status': 1,
            'current_daily_budget': Decimal('10.0000'),
            'content_ad_id': 1,
            'bid_cpc': Decimal('0.5010'),
            'supply_dash_url': None,
            'id': 1,
            'name': 'AdsNative',
            'archived': False,
            'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
            'daily_budget': Decimal('10.0000'),
            'editable_fields': {
                'state': {
                    'message': 'This source must be managed manually.',
                    'enabled': False
                },
                'bid_cpc': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                },
                'daily_budget': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                }
            },
            'state': 1,
            'maintenance': False,
            'source_id': 1,
            'current_bid_cpc': Decimal('0.5010'),
            'notifications': {},
        }, {
            'status': 2,
            'current_daily_budget': Decimal('20.0000'),
            'content_ad_id': 1,
            'bid_cpc': Decimal('0.5020'),
            'supply_dash_url': None,
            'id': 2,
            'name': 'Gravity',
            'archived': False,
            'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
            'daily_budget': Decimal('20.0000'),
            'editable_fields': {
                'state': {
                    'message': 'Please add additional budget to your campaign to make changes.',
                    'enabled': False
                },
                'bid_cpc': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                },
                'daily_budget': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                }
            },
            'state': 2,
            'maintenance': False,
            'source_id': 2,
            'current_bid_cpc': Decimal('0.5020'),
            'notifications': {},
        }])

    def test_query_ad_groups_break_source(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [{
            'status': 1,
            'archived': False,
            'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
            'name': 'AdsNative',
            'editable_fields': {
                'state': {
                    'message': 'This source must be managed manually.',
                    'enabled': False
                },
                'bid_cpc': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                },
                'daily_budget': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                }
            },
            'state': 1,
            'bid_cpc': Decimal('0.5010'),
            'current_bid_cpc': Decimal('0.5010'),
            'supply_dash_url': None,
            'maintenance': False,
            'current_daily_budget': Decimal('10.0000'),
            'source_id': 1,
            'id': 1,
            'daily_budget': Decimal('10.0000'),
            'notifications': {},
        }, {
            'status': 2,
            'archived': False,
            'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
            'name': 'Gravity',
            'editable_fields': {
                'state': {
                    'message': 'Please add additional budget to your campaign to make changes.',
                    'enabled': False
                },
                'bid_cpc': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                },
                'daily_budget': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                }
            },
            'state': 2,
            'bid_cpc': Decimal('0.5020'),
            'current_bid_cpc': Decimal('0.5020'),
            'supply_dash_url': None,
            'maintenance': False,
            'current_daily_budget': Decimal('20.0000'),
            'source_id': 2,
            'id': 2,
            'daily_budget': Decimal('20.0000'),
            'notifications': {},
        }])

    def test_query_ad_groups_break_source_content_ad(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['source_id', 'content_ad_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(pk=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'source_id': 1}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [{
            'image_hash': '100',
            'description': 'Example description',
            'content_ad_id': 1,
            'source_id': 1,
            'redirector_url': 'http://r1.zemanta.com/b/r1/z1/1/1/',
            'brand_name': 'Example',
            'image_urls': {
                'square': '/100.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                'landscape': '/100.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
            },
            'batch_name': 'batch 1',
            'archived': False,
            'name': 'Title 1',
            'display_url': 'example.com',
            'url': 'http://testurl1.com',
            'call_to_action': 'Call to action',
            'label': '',
            'state': 1,
            'status': 1,
            'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
            'batch_id': 1,
            'title': 'Title 1',
            'status_per_source': {
                1: {
                    'source_id': 1,
                    'submission_status': 1,
                    'source_name': 'AdsNative',
                    'source_status': 1,
                    'submission_errors': None
                },
            },
        }])

    def test_query_ad_groups_break_publishers(self):
        # this query is not used in the wild as we always perform RS query and than dash for publishers
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['publisher_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
                'publisher_blacklist': models.PublisherBlacklist.objects.all(),
            },
            None,
            'name', 0, 4
        )

        self.assertEqual(rows, [{
            'status': 2,
            'publisher': 'pub1.com',
            'domain': 'pub1.com',
            'source_name': 'AdsNative',
            'name': 'pub1.com',
            'exchange': 'AdsNative',
            'can_blacklist_publisher': True,
            'source_id': 1,
            'domain_link': 'http://pub1.com',
            'publisher_id': 'pub1.com__1',
            'blacklisted': 'Blacklisted'
        }, {
            'status': 2,
            'publisher': 'pub2.com',
            'domain': 'pub2.com',
            'source_name': 'Gravity',
            'name': 'pub2.com',
            'exchange': 'Gravity',
            'can_blacklist_publisher': False,
            'source_id': 2,
            'domain_link': 'http://pub2.com',
            'publisher_id': 'pub2.com__2',
            'blacklisted': 'Blacklisted'
        }, {
            'status': 2,
            'publisher': 'pub3.com',
            'domain': 'pub3.com',
            'source_name': 'AdsNative',
            'name': 'pub3.com',
            'exchange': 'AdsNative',
            'can_blacklist_publisher': True,
            'source_id': 1,
            'domain_link': 'http://pub3.com',
            'publisher_id': 'pub3.com__1',
            'blacklisted': 'Blacklisted'
        }, {
            'status': 2,
            'publisher': 'pub4.com',
            'domain': 'pub4.com',
            'source_name': 'Gravity',
            'name': 'pub4.com',
            'exchange': 'Gravity',
            'can_blacklist_publisher': False,
            'source_id': 2,
            'domain_link': 'http://pub4.com',
            'publisher_id': 'pub4.com__2',
            'blacklisted': 'Blacklisted'
        }])


@patch('dash.threads.AsyncFunction', threads.MockAsyncFunction)
@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryOrderTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_campaigns_break_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1,
             'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2,
             'campaign_has_available_budget': False, 'campaign_stop_inactive': False},
        ])

        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            '-name', 0, 2
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2,
             'campaign_has_available_budget': False, 'campaign_stop_inactive': False},
            {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1, 'state': 1,
             'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
        ])

    def test_query_campaigns_break_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None,
            '-name', 0, 2
        )

        self.assertEqual(rows,  [
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
        ])


@patch('dash.threads.AsyncFunction', threads.MockAsyncFunction)
@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryForRowsTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_for_rows_all_accounts_break_account(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'clicks': 1},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None,
            'clicks', 0, 2,
            [
                {'account_id': 1}
            ]
        )

        self.assertEqual(rows, [
            dict_join({'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_query_for_rows_all_accounts_break_account_no_rows(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None,
            'clicks', 0, 2,
            []
        )

        self.assertEqual(rows, [
            dict_join({'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_query_for_rows_all_accounts_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None, 'clicks', 0, 2,
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ]
        )

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_for_rows_all_accounts_break_source_missing_row(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None, 'clicks', 0, 2,
            [
                {'source_id': 1},
            ]
        )

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_for_rows_all_accounts_break_source_new_request(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, None, 'clicks', 1, 2,
            [
                {'source_id': 1},
            ]
        )

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_for_rows_all_accounts_break_account_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
                {'account_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'account_id': 1},
            ],
            'clicks', 0, 2,
            [
                {'account_id': 1, 'source_id': 1},
                {'account_id': 1, 'source_id': 2},
            ])

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_for_rows_all_accounts_break_account_source_missing_row(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'account_id': 1},
            ],
            'clicks', 0, 2,
            [
                {'account_id': 1, 'source_id': 1},
            ])

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_for_rows_all_accounts_break_account_source_new_request(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'account_id': 1},
            ],
            'clicks', 1, 2,
            [
                {'account_id': 1, 'source_id': 1},
            ])

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_for_rows_all_accounts_break_source_account(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
                {'account_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'account_id': 1, 'source_id': 1},
                {'account_id': 1, 'source_id': 2},
            ]
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1, 'account_id': 1, 'archived': False,
                       'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
            dict_join({'source_id': 2, 'account_id': 1, 'archived': False,
                       'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_query_for_rows_all_accounts_break_source_account_missing_row(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'account_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'account_id': 1, 'source_id': 2},
            ]
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 1, 'account_id': 1, 'archived': False,
                       'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
            dict_join({'source_id': 2, 'account_id': 1, 'archived': False,
                       'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_query_for_rows_all_accounts_break_source_account_new_request(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 1, 2,
            [
                {'account_id': 1, 'source_id': 1},
            ]
        )

        self.assertEqual(rows, [])  # all rows were already shown

    def test_query_for_rows_all_accounts_break_source_campaign(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'campaign_id': 1, 'source_id': 1},
                {'campaign_id': 1, 'source_id': 2},
            ]
        )

        self.assertEqual(rows,  [
            dict_join({'source_id': 1, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1',
                       'status': 1, 'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'source_id': 1, 'campaign_id': 2, 'archived': True, 'name': 'test campaign 2',
                       'status': 2, 'campaign_manager': 'mad.max@zemanta.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'source_id': 2, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1',
                       'status': 1, 'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_for_rows_all_accounts_break_source_campaign_no_rows(self):
        rows = api_breakdowns.query_for_rows(
            [],
            Level.ALL_ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'allowed_campaigns': models.Campaign.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [
            dict_join({'source_id': 1, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1',
                       'status': 1, 'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'source_id': 1, 'campaign_id': 2, 'archived': True, 'name': 'test campaign 2',
                       'status': 2, 'campaign_manager': 'mad.max@zemanta.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'source_id': 2, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1',
                       'status': 1, 'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_for_rows_accounts_break_campaign(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'campaign_id': 1, 'clicks': 11},
                {'campaign_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [
            dict_join({'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'campaign_id': 2, 'archived': True, 'name': 'test campaign 2', 'status': 2},
                      {'campaign_manager': 'mad.max@zemanta.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_for_rows_accounts_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_for_rows_accounts_break_campaign_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
                {'campaign_id': 2, 'source_id': 1, 'clicks': 21},
                {'campaign_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['campaign_id', 'source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'campaign_id': 1},
                {'campaign_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'campaign_id': 1, 'source_id': 1},
                {'campaign_id': 1, 'source_id': 2},
                {'campaign_id': 2, 'source_id': 1},
                {'campaign_id': 2, 'source_id': 2},
            ]
        )

        # source_id: 2 was not added to campaign
        self.assertEqual(rows,  [
            {'campaign_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'id': 1, 'source_id': 1},
            {'campaign_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'id': 2, 'source_id': 2},
            {'campaign_id': 2, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'id': 1, 'source_id': 1},
        ])

    def test_query_for_rows_accounts_break_source_campaign(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
                {'campaign_id': 2, 'source_id': 1, 'clicks': 21},
                {'campaign_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            User.objects.get(pk=1),
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
                {'campaign_id': 2, 'source_id': 1, 'clicks': 21},
                {'campaign_id': 2, 'source_id': 2, 'clicks': 22},
            ],
        )

        self.assertEqual(rows,  [
            dict_join({'campaign_id': 1, 'source_id': 1, 'archived': False,
                       'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'campaign_id': 2, 'source_id': 1, 'archived': True,
                       'name': 'test campaign 2', 'status': 2},
                      {'campaign_manager': 'mad.max@zemanta.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'campaign_id': 1, 'source_id': 2, 'archived': False,
                       'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_for_rows_campaigns_break_ad_group(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'ad_group_id': 1, 'clicks': 11},
                {'ad_group_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 1,
             'state': 1, 'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2,
             'state': 2, 'campaign_has_available_budget': False, 'campaign_stop_inactive': False},
        ])

    def test_query_for_rows_campaigns_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_for_rows_campaigns_break_ad_group_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['ad_group_id', 'source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group__campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'ad_group_id': 1},
                {'ad_group_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ]
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'ad_group_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'id': 1},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'id': 2},
        ])

    def test_query_for_rows_campaigns_break_source_ad_group(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            User.objects.get(pk=1),
            ['source_id', 'ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group__campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'source_id': 1},
                {'source_id': 2},
            ],
            'clicks', 0, 2,
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ]
        )

        self.assertEqual(rows,  [
            {'source_id': 1, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1',
             'status': 1, 'state': 1},
            {'source_id': 1, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2',
             'status': 2, 'state': 2},
            {'source_id': 2, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1',
             'status': 1, 'state': 1},
            {'source_id': 2, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2',
             'status': 2, 'state': 2},
        ])

    def test_query_for_rows_ad_groups_break_content_ad(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'content_ad_id': 1, 'clicks': 11},
                {'content_ad_id': 2, 'clicks': 22},
            ],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['content_ad_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [
            {
                'image_hash': '100',
                'description': 'Example description',
                'content_ad_id': 1,
                'redirector_url': 'http://r1.zemanta.com/b/r1/z1/1/1/',
                'brand_name': 'Example',
                'image_urls': {
                    'square': '/100.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                    'landscape': '/100.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
                },
                'batch_name': 'batch 1',
                'archived': False,
                'name': 'Title 1',
                'display_url': 'example.com',
                'url': 'http://testurl1.com',
                'call_to_action': 'Call to action',
                'label': '',
                'state': 1,
                'status': 1,
                'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
                'batch_id': 1,
                'title': 'Title 1',
                'status_per_source': {
                    1: {
                        'source_id': 1,
                        'submission_status': 1,
                        'source_name': 'AdsNative',
                        'source_status': 1,
                        'submission_errors': None
                    },
                    2: {
                        'source_id': 2,
                        'submission_status': 2,
                        'source_name': 'Gravity',
                        'source_status': 2,
                        'submission_errors': None
                    }
                },
            }, {
                'image_hash': '200',
                'description': 'Example description',
                'content_ad_id': 2,
                'redirector_url': 'http://r1.zemanta.com/b/r2/z1/1/2/',
                'brand_name': 'Example',
                'image_urls': {
                    'square': '/200.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                    'landscape': '/200.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
                },
                'batch_name': 'batch 1',
                'archived': False,
                'name': 'Title 2',
                'display_url': 'example.com',
                'url': 'http://testurl2.com',
                'call_to_action': 'Call to action',
                'label': '',
                'state': 2,
                'status': 2,
                'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
                'batch_id': 1,
                'title': 'Title 2',
                'status_per_source': {
                    2: {
                        'source_id': 2,
                        'submission_status': 2,
                        'source_name': 'Gravity',
                        'source_status': 2,
                        'submission_errors': None
                    }
                },
            },
        ])

    def test_query_for_rows_ad_groups_break_source(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['source_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [{
            'status': 1,
            'archived': False,
            'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
            'name': 'AdsNative',
            'editable_fields': {
                'state': {
                    'message': 'This source must be managed manually.',
                    'enabled': False
                },
                'bid_cpc': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                },
                'daily_budget': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                }
            },
            'state': 1,
            'bid_cpc': Decimal('0.5010'),
            'current_bid_cpc': Decimal('0.5010'),
            'supply_dash_url': None,
            'maintenance': False,
            'current_daily_budget': Decimal('10.0000'),
            'source_id': 1,
            'id': 1,
            'daily_budget': Decimal('10.0000'),
            'notifications': {},
        }, {
            'status': 2,
            'archived': False,
            'supply_dash_disabled_message': "This media source doesn't have a dashboard of its own. All campaign management is done through Zemanta One dashboard.",
            'name': 'Gravity',
            'editable_fields': {
                'state': {
                    'message': 'Please add additional budget to your campaign to make changes.',
                    'enabled': False
                },
                'bid_cpc': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                },
                'daily_budget': {
                    'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.',
                    'enabled': False
                }
            },
            'state': 2,
            'bid_cpc': Decimal('0.5020'),
            'current_bid_cpc': Decimal('0.5020'),
            'supply_dash_url': None,
            'maintenance': False,
            'current_daily_budget': Decimal('20.0000'),
            'source_id': 2,
            'id': 2,
            'daily_budget': Decimal('20.0000'),
            'notifications': {},
        }])

    def test_query_for_rows_ad_groups_break_publisher(self):
        rows = api_breakdowns.query_for_rows(
            [
                {'publisher_id': 'pub1.com__1', 'clicks': 11},
                {'publisher_id': 'pub2.com__1', 'clicks': 22},  # this one is not blacklisted
                {'publisher_id': 'pub3.com__2', 'clicks': 33},  # this one is not blacklisted
                {'publisher_id': 'pub4.com__2', 'clicks': 44},
            ],
            Level.AD_GROUPS,
            User.objects.get(pk=1),
            ['publisher_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
                'publisher_blacklist': models.PublisherBlacklist.objects.all(),
            },
            None, 'clicks', 0, 2,
            []
        )

        self.assertEqual(rows,  [{
                'status': 2,
                'publisher': 'pub1.com',
                'domain': 'pub1.com',
                'source_name': 'AdsNative',
                'name': 'pub1.com',
                'exchange': 'AdsNative',
                'can_blacklist_publisher': True,
                'source_id': 1,
                'domain_link': 'http://pub1.com',
                'publisher_id': 'pub1.com__1',
                'blacklisted': 'Blacklisted'
            }, {
                'status': 1,
                'publisher': 'pub2.com',
                'domain': 'pub2.com',
                'source_name': 'AdsNative',
                'name': 'pub2.com',
                'exchange': 'AdsNative',
                'can_blacklist_publisher': True,
                'source_id': 1,
                'domain_link': 'http://pub2.com',
                'publisher_id': 'pub2.com__1',
                'blacklisted': 'Active'
            }, {
                'status': 1,
                'publisher': 'pub3.com',
                'domain': 'pub3.com',
                'source_name': 'Gravity',
                'name': 'pub3.com',
                'exchange': 'Gravity',
                'can_blacklist_publisher': False,
                'source_id': 2,
                'domain_link': 'http://pub3.com',
                'publisher_id': 'pub3.com__2',
                'blacklisted': 'Active'
            }, {
                'status': 2,
                'publisher': 'pub4.com',
                'domain': 'pub4.com',
                'source_name': 'Gravity',
                'name': 'pub4.com',
                'exchange': 'Gravity',
                'can_blacklist_publisher': False,
                'source_id': 2,
                'domain_link': 'http://pub4.com',
                'publisher_id': 'pub4.com__2',
                'blacklisted': 'Blacklisted'
            }])


class HelpersTest(TestCase):

    def test_get_adjusted_limits_for_additional_rows(self):

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows(range(5), range(5), 0, 10), (0, 5))

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows([], range(5), 5, 10), (0, 10))

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows([], range(5), 10, 10), (5, 10))

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows(range(5), range(15), 10, 10), (0, 5))

    def test_get_default_order(self):

        self.assertEquals(api_breakdowns.get_default_order('source_id', '-clicks'), ['-name', '-source_id'])

        self.assertEquals(api_breakdowns.get_default_order('source_id', 'clicks'), ['name', 'source_id'])

        self.assertEquals(api_breakdowns.get_default_order('ad_group_id', 'clicks'), ['name', 'ad_group_id'])

    def test_make_rows(self):
        self.assertItemsEqual(augmenter.make_dash_rows('account_id', [1, 2, 3], None), [
            {'account_id': 1},
            {'account_id': 2},
            {'account_id': 3},
        ])

        self.assertItemsEqual(augmenter.make_dash_rows('account_id', [1, 2, 3], {'source_id': 2}), [
            {'account_id': 1, 'source_id': 2},
            {'account_id': 2, 'source_id': 2},
            {'account_id': 3, 'source_id': 2},
        ])
