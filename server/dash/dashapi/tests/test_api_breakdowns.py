import datetime
from decimal import Decimal

from django.test import TestCase, override_settings

from utils.dict_helper import dict_join
from dash.dashapi.tests.test_queries import extract_keys

from dash import models
from dash.constants import Level
from dash.dashapi import api_breakdowns
from dash.dashapi import helpers


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


@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_query_all_accounts_break_account(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
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
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1, 'state': 1,
             'daily_budget': Decimal('50.0000'), 'min_bid_cpc': 0.12, 'max_bid_cpc': 0.12},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2, 'state': 2,
             'daily_budget': None, 'min_bid_cpc': None, 'max_bid_cpc': None},
        ])

    def test_query_all_accounts_break_account_source(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'account_id': 1}],
            'name', 0, 2
        )

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1,
             'status': 1, 'state': 1, 'daily_budget': Decimal('50.0000'), 'min_bid_cpc': 0.12, 'max_bid_cpc': 0.12},
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2,
             'status': 2, 'state': 2, 'daily_budget': None, 'min_bid_cpc': None, 'max_bid_cpc': None},
        ])

    def test_query_all_accounts_break_source_account(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
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
            dict_join({'source_id': 2, 'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 2},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_query_all_accounts_break_source_campaign(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
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
            dict_join({'source_id': 2, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 2},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_all_accounts_break_account_campaign(self):
        rows = api_breakdowns.query(
            Level.ALL_ACCOUNTS,
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
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1, 'state': 1,
             'min_bid_cpc': 0.12, 'max_bid_cpc': 0.12, 'daily_budget': Decimal('50.0000')},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2, 'state': 2,
             'min_bid_cpc': None, 'max_bid_cpc': None, 'daily_budget': None},
        ])

    def test_query_accounts_break_campaign_source(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
            ['campaign_id', 'source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'campaign_id': 1}, {'campaign_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'campaign_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1, 'state': 1,
             'min_bid_cpc': 0.12, 'max_bid_cpc': 0.12, 'daily_budget': Decimal('50.0000')},
            {'campaign_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2, 'state': 2,
             'min_bid_cpc': None, 'max_bid_cpc': None, 'daily_budget': None},
        ])

    def test_query_accounts_break_source_campaign(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
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
            dict_join({'source_id': 2, 'campaign_id': 1, 'archived': False, 'name': 'test campaign 1', 'status': 2},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_query_accounts_break_source_ad_group(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
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
            {'source_id': 2, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 2, 'state': 2},
            {'source_id': 2, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2},
        ])

    def test_query_accounts_break_campaign_ad_group_not_allowed(self):
        rows = api_breakdowns.query(
            Level.ACCOUNTS,
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
             'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
        ])

    def test_query_campaigns_break_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
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
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1, 'state': 1,
             'min_bid_cpc': 0.12, 'max_bid_cpc': 0.12, 'daily_budget': Decimal('50.0000')},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2, 'state': 2,
             'min_bid_cpc': None, 'max_bid_cpc': None, 'daily_budget': None},
        ])

    def test_query_campaigns_break_ad_group_source(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
            ['ad_group_id', 'source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [{'ad_group_id': 1}, {'ad_group_id': 2}],
            'name', 0, 2
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1,
             'status': 1, 'state': 1, 'min_bid_cpc': 0.12, 'max_bid_cpc': 0.12, 'daily_budget': Decimal('50.0000')},
            {'ad_group_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2,
             'status': 2, 'state': 2, 'min_bid_cpc': None, 'max_bid_cpc': None, 'daily_budget': None},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1,
             'status': 2, 'state': 1, 'min_bid_cpc': None, 'max_bid_cpc': None, 'daily_budget': None},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2,
             'status': 2, 'state': 2, 'min_bid_cpc': None, 'max_bid_cpc': None, 'daily_budget': None},
        ])

    def test_query_campaigns_break_source_ad_group(self):
        rows = api_breakdowns.query(
            Level.CAMPAIGNS,
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
            {'source_id': 2, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1', 'status': 2, 'state': 2},
            {'source_id': 2, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2, 'state': 2},
        ])

    def test_query_ad_groups_break_content_ad(self):
        rows = api_breakdowns.query(
            Level.AD_GROUPS,
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
            },
        ])


@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class AugmentTest(TestCase):

    fixtures = ['test_api_breakdowns.yaml']

    def test_augment_all_accounts_break_account(self):
        rows = api_breakdowns.augment(
            [
                {'account_id': 1, 'clicks': 1},
            ],
            Level.ALL_ACCOUNTS,
            ['account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            })

        self.assertEqual(rows, [
            dict_join({'account_id': 1, 'clicks': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_augment_all_accounts_break_source(self):
        rows = api_breakdowns.augment(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.ALL_ACCOUNTS,
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            })

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1,
             'state': 1, 'clicks': 11, 'daily_budget': Decimal('50.0000'), 'min_bid_cpc': 0.12, 'max_bid_cpc': 0.12},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2,
             'state': 2, 'clicks': 22, 'daily_budget': None, 'min_bid_cpc': None, 'max_bid_cpc': None},
        ])

    def test_augment_all_accounts_break_account_source(self):
        rows = api_breakdowns.augment(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
                {'account_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            })

        self.assertEqual(rows, [
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1,
             'state': 1, 'clicks': 11, 'daily_budget': Decimal('50.0000'), 'min_bid_cpc': 0.12, 'max_bid_cpc': 0.12},
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2,
             'state': 2, 'clicks': 12, 'daily_budget': None, 'min_bid_cpc': None, 'max_bid_cpc': None},
        ])

    def test_augment_all_accounts_break_source_account(self):
        rows = api_breakdowns.augment(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
                {'account_id': 1, 'source_id': 2, 'clicks': 12},
            ],
            Level.ALL_ACCOUNTS,
            ['source_id', 'account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            })

        self.assertEqual(rows, [
            dict_join({'source_id': 1, 'account_id': 1, 'clicks': 11, 'archived': False,
                       'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
            dict_join({'source_id': 2, 'account_id': 1, 'clicks': 12, 'archived': False,
                       'name': 'test account 1', 'status': 2},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_augment_accounts_break_campaign(self):
        rows = api_breakdowns.augment(
            [
                {'campaign_id': 1, 'clicks': 11},
                {'campaign_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            ['campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            }
        )

        self.assertEqual(rows,  [
            dict_join({'campaign_id': 1, 'clicks': 11, 'archived': False, 'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'campaign_id': 2, 'clicks': 22, 'archived': True, 'name': 'test campaign 2', 'status': 2},
                      {'campaign_manager': 'mad.max@zemanta.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_augment_accounts_break_source(self):
        rows = api_breakdowns.augment(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            ['source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign__account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            }
        )

        self.assertEqual(rows,  [
            {'clicks': 11, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1,
             'status': 1, 'state': 1, 'daily_budget': Decimal('50.0000'), 'min_bid_cpc': 0.12,
             'max_bid_cpc': 0.12},
            {'clicks': 22, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2,
             'status': 2, 'state': 2, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
        ])

    def test_augment_accounts_break_campaign_source(self):
        rows = api_breakdowns.augment(
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
                {'campaign_id': 2, 'source_id': 1, 'clicks': 21},
                {'campaign_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            ['campaign_id', 'source_id'],
            {
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
        )

        self.assertEqual(rows,  [
            {'campaign_id': 1, 'clicks': 11, 'archived': False, 'maintenance': False, 'name': 'AdsNative',
             'source_id': 1, 'status': 1, 'state': 1, 'daily_budget': Decimal('50.0000'), 'min_bid_cpc': 0.12,
             'max_bid_cpc': 0.12},
            {'campaign_id': 1, 'clicks': 12, 'archived': False, 'maintenance': False, 'name': 'Gravity',
             'source_id': 2, 'status': 2, 'state': 2, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
            {'campaign_id': 2, 'clicks': 21, 'archived': False, 'maintenance': False, 'name': 'AdsNative',
             'source_id': 1, 'status': 2, 'state': 2, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
            {'campaign_id': 2, 'clicks': 22, 'archived': False, 'maintenance': False, 'name': 'Gravity',
             'source_id': 2, 'status': 2, 'state': 2, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
        ])

    def test_augment_accounts_break_source_campaign(self):
        rows = api_breakdowns.augment(
            [
                {'campaign_id': 1, 'source_id': 1, 'clicks': 11},
                {'campaign_id': 1, 'source_id': 2, 'clicks': 12},
                {'campaign_id': 2, 'source_id': 1, 'clicks': 21},
                {'campaign_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.ACCOUNTS,
            ['source_id', 'campaign_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': models.Campaign.objects.filter(account_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
        )

        self.assertEqual(rows,  [
            dict_join({'campaign_id': 1, 'source_id': 1, 'clicks': 11, 'archived': False,
                       'name': 'test campaign 1', 'status': 1},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'campaign_id': 1, 'source_id': 2, 'clicks': 12, 'archived': False,
                       'name': 'test campaign 1', 'status': 2},
                      {'campaign_manager': 'supertestuser@test.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'campaign_id': 2, 'source_id': 1, 'clicks': 21, 'archived': True,
                       'name': 'test campaign 2', 'status': 2},
                      {'campaign_manager': 'mad.max@zemanta.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
            dict_join({'campaign_id': 2, 'source_id': 2, 'clicks': 22, 'archived': True,
                       'name': 'test campaign 2', 'status': 2},
                      {'campaign_manager': 'mad.max@zemanta.com'},
                      EMPTY_CAMPAIGN_PROJECTIONS),
        ])

    def test_augment_campaigns_break_ad_group(self):
        rows = api_breakdowns.augment(
            [
                {'ad_group_id': 1, 'clicks': 11},
                {'ad_group_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'clicks': 11, 'archived': False, 'name': 'test adgroup 1', 'status': 1,
             'state': 1, 'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
            {'ad_group_id': 2, 'clicks': 22, 'archived': False, 'name': 'test adgroup 2', 'status': 2,
             'state': 2, 'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
        ])

    def test_augment_campaigns_break_source(self):
        rows = api_breakdowns.augment(
            [
                {'source_id': 1, 'clicks': 11},
                {'source_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
        )

        self.assertEqual(rows,  [
            {'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1, 'status': 1,
             'state': 1, 'clicks': 11, 'daily_budget': Decimal('50.0000'), 'min_bid_cpc': 0.12, 'max_bid_cpc': 0.12},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2,
             'state': 2, 'clicks': 22, 'daily_budget': None, 'min_bid_cpc': None, 'max_bid_cpc': None},
        ])

    def test_augment_campaigns_break_ad_group_source(self):
        rows = api_breakdowns.augment(
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            ['ad_group_id', 'source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1,
             'status': 1, 'clicks': 11, 'state': 1, 'daily_budget': Decimal('50.0000'), 'min_bid_cpc': 0.12,
             'max_bid_cpc': 0.12},
            {'ad_group_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2,
             'status': 2, 'clicks': 12, 'state': 2, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1,
             'status': 2, 'clicks': 21, 'state': 1, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2,
             'status': 2, 'clicks': 22, 'state': 2, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
        ])

    def test_augment_campaigns_break_source_ad_group(self):
        rows = api_breakdowns.augment(
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
                {'ad_group_id': 1, 'source_id': 2, 'clicks': 12},
                {'ad_group_id': 2, 'source_id': 1, 'clicks': 21},
                {'ad_group_id': 2, 'source_id': 2, 'clicks': 22},
            ],
            Level.CAMPAIGNS,
            ['source_id', 'ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'allowed_content_ads': models.ContentAd.objects.filter(ad_group__campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            }
        )

        self.assertEqual(rows,  [
            {'source_id': 1, 'ad_group_id': 1, 'clicks': 11, 'archived': False, 'name': 'test adgroup 1',
             'status': 1, 'state': 1},
            {'source_id': 2, 'ad_group_id': 1, 'clicks': 12, 'archived': False, 'name': 'test adgroup 1',
             'status': 2, 'state': 2},
            {'source_id': 1, 'ad_group_id': 2, 'clicks': 21, 'archived': False, 'name': 'test adgroup 2',
             'status': 2, 'state': 2},
            {'source_id': 2, 'ad_group_id': 2, 'clicks': 22, 'archived': False, 'name': 'test adgroup 2',
             'status': 2, 'state': 2},
        ])

    def test_augment_ad_groups_break_content_ad(self):
        rows = api_breakdowns.augment(
            [
                {'content_ad_id': 1, 'clicks': 11},
                {'content_ad_id': 2, 'clicks': 22},
            ],
            Level.AD_GROUPS,
            ['content_ad_id'],
            {
                'ad_group': models.AdGroup.objects.get(pk=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
        )

        self.assertEqual(rows,  [
            {
                'clicks': 11,
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
            }, {
                'clicks': 22,
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
            },
        ])


@override_settings(R1_BLANK_REDIRECT_URL='http://r1.zemanta.com/b/{redirect_id}/z1/1/{content_ad_id}/')
class QueryMissingRowsTest(TestCase):
    """
    *_filled_sometimeago tests try to test the case when stats rows were retrieved in previous
    requests, not in current one.
    """

    fixtures = ['test_api_breakdowns.yaml']

    def test_all_accounts_break_account(self):
        rows = api_breakdowns.query_missing_rows(
            [],
            Level.ALL_ACCOUNTS,
            ['account_id'],
            {
                'date__gte': datetime.date(2016, 7, 1),
                'date__lte': datetime.date(2016, 7, 31),
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, [], 'name', 0, 10,
            []
        )

        self.assertEqual(rows, [
            dict_join({'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 1},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_all_accounts_break_account_filled_sometimeago(self):
        rows = api_breakdowns.query_missing_rows(
            [],
            Level.ALL_ACCOUNTS,
            ['account_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, [], 'name', 0, 10,
            [{'account_id': 1}]
        )

        self.assertEqual(rows, [])

    def test_all_accounts_break_source(self):
        rows = api_breakdowns.query_missing_rows(
            [
                {'source_id': 1, 'clicks': 11},
            ],
            Level.ALL_ACCOUNTS,
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, [], 'name', 0, 10,
            [{'source_id': 1}]
        )

        self.assertEqual(rows, [
            {'source_id': 1, 'clicks': 11},  # does not augment existing rows
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2,
             'state': 2, 'daily_budget': None, 'min_bid_cpc': None, 'max_bid_cpc': None},  # no stats -> no clicks
        ])

    def test_all_accounts_break_source_filled_sometimeago(self):
        rows = api_breakdowns.query_missing_rows(
            [],
            Level.ALL_ACCOUNTS,
            ['source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            }, [], 'name', 0, 10,
            [{'source_id': 1}]
        )

        self.assertEqual(rows, [
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2,
             'state': 2, 'daily_budget': None, 'min_bid_cpc': None, 'max_bid_cpc': None},  # no stats -> no clicks
        ])

    def test_all_accounts_break_account_source(self):
        rows = api_breakdowns.query_missing_rows(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
            ],
            Level.ALL_ACCOUNTS,
            ['account_id', 'source_id'],
            {
                'allowed_accounts': models.Account.objects.all(),
                'show_archived': False,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'account_id': 1},
            ], 'name', 0, 10,
            [{'account_id': 1, 'source_id': 1}]
        )

        self.assertEqual(rows, [
            {'account_id': 1, 'source_id': 1, 'clicks': 11},
            {'account_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2,
             'state': 2, 'daily_budget': None, 'min_bid_cpc': None, 'max_bid_cpc': None},
        ])

    def test_all_accounts_break_source_account(self):
        rows = api_breakdowns.query_missing_rows(
            [
                {'account_id': 1, 'source_id': 1, 'clicks': 11},
            ],
            Level.ALL_ACCOUNTS,
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
            'name', 0, 10,
            [{'account_id': 1, 'source_id': 1}]
        )

        self.assertEqual(rows, [
            dict_join({'account_id': 1, 'source_id': 1, 'clicks': 11}),
            dict_join({'source_id': 2, 'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 2},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_all_accounts_break_source_account_filled_sometimeago(self):
        rows = api_breakdowns.query_missing_rows(
            [],
            Level.ALL_ACCOUNTS,
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
            'name', 0, 10,
            [{'account_id': 1, 'source_id': 1}]
        )

        self.assertEqual(rows, [
            dict_join({'source_id': 2, 'account_id': 1, 'archived': False, 'name': 'test account 1', 'status': 2},
                      {'default_account_manager': 'mad.max@zemanta.com',
                       'default_sales_representative': 'supertestuser@test.com',
                       'agency': '', 'account_type': 'Self-managed'},
                      EMPTY_ACCOUNT_PROJECTIONS),
        ])

    def test_campaigns_break_ad_group(self):
        rows = api_breakdowns.query_missing_rows(
            [
                {'ad_group_id': 1, 'clicks': 11},
            ],
            Level.CAMPAIGNS,
            ['ad_group_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            }, [], 'name', 0, 10,
            [{'ad_group_id': 1}]
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'clicks': 11},
            {'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2', 'status': 2,
             'state': 2, 'campaign_has_available_budget': False, 'campaign_stop_inactive': True},
        ])

    def test_campaigns_break_source(self):
        rows = api_breakdowns.query_missing_rows(
            [
                {'source_id': 1, 'clicks': 11},
            ],
            Level.CAMPAIGNS,
            ['source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            }, [], 'name', 0, 10,
            [{'source_id': 1}]
        )

        self.assertEqual(rows,  [
            {'source_id': 1, 'clicks': 11},
            {'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2, 'status': 2,
             'state': 2, 'daily_budget': None, 'min_bid_cpc': None, 'max_bid_cpc': None},
        ])

    def test_campaigns_break_ad_group_source(self):
        rows = api_breakdowns.query_missing_rows(
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
            ],
            Level.CAMPAIGNS,
            ['ad_group_id', 'source_id'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': models.AdGroup.objects.filter(campaign_id=1),
                'show_archived': True,
                'filtered_sources': models.Source.objects.all(),
            },
            [
                {'ad_group_id': 1},
                {'ad_group_id': 2},
            ], 'name', 0, 10,
            [{'ad_group_id': 1, 'source_id': 1}]
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
            {'ad_group_id': 1, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2,
             'status': 2, 'state': 2, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'AdsNative', 'source_id': 1,
             'status': 2, 'state': 1, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
            {'ad_group_id': 2, 'archived': False, 'maintenance': False, 'name': 'Gravity', 'source_id': 2,
             'status': 2, 'state': 2, 'daily_budget': None, 'min_bid_cpc': None,
             'max_bid_cpc': None},
        ])

    def test_campaigns_break_source_ad_group(self):
        rows = api_breakdowns.query_missing_rows(
            [
                {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
            ],
            Level.CAMPAIGNS,
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
            ], 'name', 0, 10,
            [{'ad_group_id': 1, 'source_id': 1}]
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'source_id': 1, 'clicks': 11},
            {'source_id': 1, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2',
             'status': 2, 'state': 2},
            {'source_id': 2, 'ad_group_id': 1, 'archived': False, 'name': 'test adgroup 1',
             'status': 2, 'state': 2},
            {'source_id': 2, 'ad_group_id': 2, 'archived': False, 'name': 'test adgroup 2',
             'status': 2, 'state': 2},
        ])

    def test_campaigns_break_ad_group_content_ads(self):
        rows = api_breakdowns.query_missing_rows(
            [
                {'ad_group_id': 1, 'content_ad_id': 1, 'clicks': 11},
            ],
            Level.CAMPAIGNS,
            ['ad_group_id', 'content_ad_id'],
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
            ], 'name', 0, 10,
            [{'ad_group_id': 1, 'content_ad_id': 1}]
        )

        self.assertEqual(rows,  [
            {'ad_group_id': 1, 'content_ad_id': 1, 'clicks': 11},
            {
                'status': 2,
                'image_hash': '200',
                'description': 'Example description',
                'content_ad_id': 2,
                'redirector_url': 'http://r1.zemanta.com/b/r2/z1/1/2/',
                'brand_name': 'Example',
                'image_urls': {
                    'square': '/200.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                    'landscape': '/200.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
                },
                'ad_group_id': 1,
                'batch_name': 'batch 1',
                'archived': False,
                'name': 'Title 2',
                'display_url': 'example.com',
                'url': 'http://testurl2.com',
                'call_to_action': 'Call to action',
                'label': '',
                'state': 2,
                'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
                'batch_id': 1,
                'title': 'Title 2'
            }, {
                'status': 2,
                'image_hash': '300',
                'description': 'Example description',
                'content_ad_id': 3,
                'redirector_url': 'http://r1.zemanta.com/b/None/z1/1/3/',
                'brand_name': 'Example',
                'image_urls': {
                    'square': '/300.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                    'landscape': '/300.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'
                },
                'ad_group_id': 1,
                'batch_name': 'batch 2',
                'archived': True,
                'name': 'Title 3',
                'display_url': 'example.com',
                'url': 'http://testurl3.com',
                'call_to_action': 'Call to action',
                'label': '',
                'state': 2,
                'upload_time': datetime.datetime(2015, 2, 23, 0, 0),
                'batch_id': 2,
                'title': 'Title 3'
            }])


class HelpersTest(TestCase):

    def test_get_adjusted_limits_for_additional_rows(self):

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows(range(5), range(5), 0, 10), (0, 5))

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows([], range(5), 5, 10), (0, 10))

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows([], range(5), 10, 10), (5, 10))

        self.assertEquals(helpers.get_adjusted_limits_for_additional_rows(range(5), range(15), 10, 10), (0, 5))
