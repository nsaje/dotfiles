import json
import datetime
from mock import patch, ANY

from django.test import TestCase, Client
from django.http.request import HttpRequest
from django.core.urlresolvers import reverse

from zemauth.models import User
from utils import test_helper
from stats.helpers import Goals

from dash import models
from dash.views import breakdown
from dash.views import breakdown_helpers
from dash import table
from dash.constants import Level


class ExtractConstraintsTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def test_extract_constraints(self):
        form_data = {
            'breakdown': ['account', 'source', 'dma', 'day'],
            'start_date': datetime.date(2016, 1, 1),
            'end_date': datetime.date(2016, 2, 3),
            'filtered_sources': models.Source.objects.filter(pk=1),
            'show_archived': True,
            'parents': ['123', '323'],
            'offset': 12,
            'limit': 20,
            'order': '-clicks',
        }

        user = User.objects.get(pk=1)

        self.assertDictEqual(breakdown.extract_constraints(form_data, Level.ALL_ACCOUNTS, user, []), {
            'date__gte': datetime.date(2016, 1, 1),
            'date__lte': datetime.date(2016, 2, 3),
            'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.filter(pk=1)),
            'show_archived': True,
            'allowed_accounts': test_helper.QuerySetMatcher(models.Account.objects.all()),
        })

    def test_add_kwargs(self):
        form_data = {
            'breakdown': ['account', 'source', 'dma', 'day'],
            'start_date': datetime.date(2016, 1, 1),
            'end_date': datetime.date(2016, 2, 3),
            'filtered_sources': models.Source.objects.filter(pk=1),
            'show_archived': True,
            'parents': ['123', '323'],
            'offset': 12,
            'limit': 20,
            'order': '-clicks',
        }

        user = User.objects.get(pk=1)
        self.assertDictEqual(
            breakdown.extract_constraints(
                form_data, Level.ACCOUNTS, user, ['account_id'],
                account=models.Account.objects.get(pk=1),
            ),
            {
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.filter(pk=1)),
                'show_archived': True,
                'account': models.Account.objects.get(pk=1),
                'allowed_campaigns': test_helper.QuerySetMatcher(models.Campaign.objects.all()),
                'allowed_ad_groups': test_helper.QuerySetMatcher(models.AdGroup.objects.all()),
            }
        )


@patch('stats.api_breakdowns.query')
class AllAccountsBreakdownTestCase(TestCase):
    fixtures = ['test_api', 'test_views', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_permission(self, mock_query):
        url = reverse('breakdown_all_accounts', kwargs={
            'breakdown': '/account/campaign/dma/day'
        })

        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_post(self, mock_query):
        mock_query.return_value = {}

        test_helper.add_permissions(self.user, [
            'can_access_table_breakdowns_feature', 'all_accounts_accounts_view', 'can_view_breakdown_by_delivery'])

        params = {
            'limit': 5,
            'offset': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': ['1', '3', '4'],
            'show_archived': 'true',
            'parents': ['1-2-33', '1-2-34', '1-3-22'],
        }

        response = self.client.post(
            reverse('breakdown_all_accounts', kwargs={
                'breakdown': '/account/campaign/dma/day'
            }),
            data=json.dumps({'params': params}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.ALL_ACCOUNTS,
            self.user,
            ['account_id', 'campaign_id', 'dma', 'day'],
            {
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                'show_archived': True,
                'allowed_accounts': test_helper.QuerySetMatcher(models.Account.objects.filter(pk=1)),
                'allowed_campaigns': test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1, 2])),
            },
            ANY,
            ['1-2-33', '1-2-34', '1-3-22'],
            '-clicks',
            33,
            5 + breakdown.REQUEST_LIMIT_OVERFLOW  # [workaround] see implementation
        )

    @patch.object(table.AccountsAccountsTable, 'get')
    def test_post_base_level(self, mock_table, mock_query):
        mock_table.return_value = {
            'order': '-clicks',
            'pagination': {
                'numPages': 10,
                'count': 40,
                'endIndex': 4,
                'startIndex': 1,
                'currentPage': 1,
                'size': 4
            },
            'totals': None,
            'rows': [{
                'account': 11,
                'account_type': 'Managed',
                'agency': '',
                'archived': False,
                'click_discrepancy': 40.6292995154633,
                'ctr': 0.746625150795136,
                'default_account_manager': 'Ana Dejanovi\xc4\x87',
                'default_sales_representative': 'John Castiglione',
                'id': '11',
                'impressions': 42541160,
                'name': 'BuildDirect',
                'pv_per_visit': 1.18423969243007,
                'status': 1,
            }, {
                'account': 116,
                'account_type': 'Self-managed',
                'agency': 'MBuy',
                'archived': False,
                'click_discrepancy': None,
                'ctr': 0.682212242285772,
                'default_account_manager': 'Helen Wagner',
                'default_sales_representative': 'David Kaplan',
                'id': '116',
                'impressions': 9484585,
                'name': "Cat's Pride",
                'pv_per_visit': None,
                'status': 1,
            }, {
                'account': 305,
                'account_type': 'Pilot',
                'agency': '',
                'archived': False,
                'click_discrepancy': None,
                'ctr': 0.445301342321372,
                'default_account_manager': 'Tadej Pavli\xc4\x8d',
                'default_sales_representative': 'David Kaplan',
                'id': '305',
                'impressions': 13136273,
                'name': 'Outbrain',
                'pv_per_visit': None,
                'status': 1,
            }, {
                'account': 63,
                'account_type': 'Managed',
                'agency': '',
                'archived': False,
                'click_discrepancy': 28.166866857618,
                'ctr': 0.374501558123542,
                'default_account_manager': 'Ana Dejanovi\xc4\x87',  # TODO this should be unicode
                'default_sales_representative': 'David Kaplan',
                'id': '63',
                'impressions': 23119797,
                'name': 'Allstate',
                'pv_per_visit': 1.22613994469098,
                'status': 1,
            }],
        }

        test_helper.add_permissions(self.user, ['can_access_table_breakdowns_feature', 'all_accounts_accounts_view'])

        params = {
            'limit': 2,
            'offset': 1,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': ['1', '3', '4'],
            'show_archived': 'true',
            'parents': None,
        }

        response = self.client.post(
            reverse('breakdown_all_accounts', kwargs={
                'breakdown': '/account'
            }),
            data=json.dumps({'params': params}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)

        self.assertIsNone(result['data'][0]['breakdown_id'])

        self.assertDictEqual(result['data'][0]['pagination'], {
            'count': 40,
            'limit': 2,
            'offset': 1,
        })

        self.assertEqual(len(result['data']), 1)

        self.assertItemsEqual(result['data'][0]['rows'], [{
            u'account': 116,
            u'account_type': u'Self-managed',
            u'agency': u'MBuy',
            u'archived': False,
            u'breakdown_id': u'116',
            u'breakdown_name': u"Cat's Pride",
            u'click_discrepancy': None,
            u'ctr': 0.682212242285772,
            u'default_account_manager': u'Helen Wagner',
            u'default_sales_representative': u'David Kaplan',
            u'id': u'116',
            u'impressions': 9484585,
            u'name': u"Cat's Pride",
            u'parent_breakdown_id': None,
            u'pv_per_visit': None,
            u'status': {'value': 1},
        }, {
            u'account': 305,  # TODO remove when doing stats
            u'account_type': u'Pilot',
            u'agency': u'',
            u'archived': False,
            u'breakdown_id': u'305',
            u'breakdown_name': u'Outbrain',
            u'click_discrepancy': None,
            u'ctr': 0.445301342321372,
            u'default_account_manager': u'Tadej Pavli\u010d',
            u'default_sales_representative': u'David Kaplan',
            u'id': u'305',  # TODO remove when doing stats
            u'impressions': 13136273,
            u'name': u'Outbrain',
            u'parent_breakdown_id': None,
            u'pv_per_visit': None,
            u'status': {'value': 1},
        }])


@patch('stats.api_breakdowns.query')
class AccountBreakdownTestCase(TestCase):
    fixtures = ['test_api', 'test_views', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_permission(self, mock_query):
        url = reverse('breakdown_accounts', kwargs={
            'account_id': 1,
            'breakdown': '/campaign/dma/day'
        })

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    def test_post(self, mock_query):
        test_helper.add_permissions(self.user, [
            'can_access_table_breakdowns_feature', 'account_campaigns_view', 'can_view_breakdown_by_delivery'])

        mock_query.return_value = {}

        params = {
            'limit': 5,
            'offset': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': ['1', '3', '4'],
            'show_archived': 'true',
            'parents': ['1-2-33', '1-2-34', '1-3-22'],
        }

        response = self.client.post(
            reverse('breakdown_accounts', kwargs={
                'account_id': 1,
                'breakdown': '/campaign/source/dma/day'
            }),
            data=json.dumps({'params': params}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.ACCOUNTS,
            self.user,
            ['campaign_id', 'source_id', 'dma', 'day'],
            {
                'account': models.Account.objects.get(pk=1),
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                'allowed_campaigns': test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1, 2])),
                'allowed_ad_groups': test_helper.QuerySetMatcher(models.AdGroup.objects.filter(pk__in=[1, 2, 9, 10])),
                'show_archived': True,
            },
            ANY,
            ['1-2-33', '1-2-34', '1-3-22'],
            '-clicks',
            33,
            5 + breakdown.REQUEST_LIMIT_OVERFLOW  # [workaround] see implementation
        )

    @patch.object(table.AccountCampaignsTable, 'get')
    def test_post_base_level(self, mock_table, mock_query):
        test_helper.add_permissions(self.user, ['can_access_table_breakdowns_feature', 'account_campaigns_view'])

        mock_table.return_value = {
            'rows': [{
                'pageviews': 92569,
                'campaign': 350,
                'cost': 10612.4835,
                'impressions': 19996915,
                'archived': False,
                'state': 1,
                'campaign_manager': 'Ana Dejanovi\xc4\x87',
                'name': u'Blog Campaign [Mobile]',
            }, {
                'pageviews': 78853,
                'campaign': 198,
                'cost': 9196.1064,
                'impressions': 9621740,
                'archived': False,
                'state': 1,
                'campaign_manager': 'Ana Dejanovi\xc4\x87',
                'name': u'Blog Campaign [Desktop]',
            }, {
                'pageviews': 51896,
                'campaign': 413,
                'cost': 7726.1054,
                'impressions': 10441143,
                'archived': False,
                'state': 1,
                'campaign_manager': 'Ana Dejanovi\xc4\x87',
                'name': u'Learning Center',
            }, {
                'pageviews': None,
                'campaign': 357,
                'cost': 1766.137,
                'impressions': 2481362,
                'archived': False,
                'state': 1,
                'campaign_manager': 'Ana Dejanovi\xc4\x87',
                'name': u'Earned Media',
            }],
            'incomplete_postclick_metrics': False,
            'is_sync_recent': True,
            'last_sync': None,
            'is_sync_in_progress': False,
            'totals': {
                'pageviews': 223318,
                'cost': 29300.8323,
                'impressions': 42541160,
            },
            'order': u'-media_cost'
        }

        params = {
            'limit': 2,
            'offset': 1,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': ['1', '3', '4'],
            'show_archived': 'true',
            'parents': None,
        }

        response = self.client.post(
            reverse('breakdown_accounts', kwargs={
                'account_id': 1,
                'breakdown': '/campaign'
            }),
            data=json.dumps({'params': params}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)

        self.assertIsNone(result['data'][0]['breakdown_id'])

        self.assertDictEqual(result['data'][0]['pagination'], {
            'count': 4,
            'limit': 2,
            'offset': 1,
        })

        self.assertEqual(len(result['data']), 1)

        self.assertItemsEqual(result['data'][0]['rows'], [{
            u'id': 198,
            u'breakdown_id': u'198',
            u'breakdown_name': u'Blog Campaign [Desktop]',
            u'parent_breakdown_id': None,
            u'archived': False,
            u'campaign': 198,
            u'campaign_manager': u'Ana Dejanovi\u0107',
            u'cost': 9196.1064,
            u'impressions': 9621740,
            u'name': u'Blog Campaign [Desktop]',
            u'pageviews': 78853,
            u'status': {'value': 1},
        }, {
            u'id': 413,
            u'breakdown_id': u'413',
            u'breakdown_name': u'Learning Center',
            u'parent_breakdown_id': None,
            u'archived': False,
            u'campaign': 413,  # TODO remove when doing stats
            u'campaign_manager': u'Ana Dejanovi\u0107',
            u'cost': 7726.1054,
            u'impressions': 10441143,
            u'name': u'Learning Center',  # TODO remove when doing stats
            u'pageviews': 51896,
            u'status': {'value': 1},
        }])


@patch('stats.api_breakdowns.query')
class CampaignBreakdownTestCase(TestCase):
    fixtures = ['test_api', 'test_views', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_permission(self, mock_query):
        url = reverse('breakdown_campaigns', kwargs={
            'campaign_id': 1,
            'breakdown': '/ad_group/dma/day'
        })

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    def test_post(self, mock_query):
        test_helper.add_permissions(self.user, [
            'can_access_table_breakdowns_feature', 'can_view_breakdown_by_delivery'])

        mock_query.return_value = {}

        params = {
            'limit': 5,
            'offset': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': ['1', '3', '4'],
            'show_archived': 'false',
            'parents': ['1-2-33', '1-2-34', '1-3-22'],
        }

        response = self.client.post(
            reverse('breakdown_campaigns', kwargs={
                'campaign_id': 1,
                'breakdown': '/ad_group/source/dma/day'
            }),
            data=json.dumps({'params': params}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        ad_groups = models.Campaign.objects.get(pk=1).adgroup_set.all().exclude_archived()
        content_ads = models.ContentAd.objects.filter(ad_group__in=ad_groups).exclude_archived()

        mock_query.assert_called_with(
            Level.CAMPAIGNS,
            self.user,
            ['ad_group_id', 'source_id', 'dma', 'day'],
            {
                'campaign': models.Campaign.objects.get(pk=1),
                'account': models.Account.objects.get(pk=1),
                'allowed_ad_groups': test_helper.QuerySetMatcher(ad_groups),
                'allowed_content_ads': test_helper.QuerySetMatcher(content_ads),
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                'show_archived': False,
            },
            ANY,
            ['1-2-33', '1-2-34', '1-3-22'],
            '-clicks',
            33,
            5 + breakdown.REQUEST_LIMIT_OVERFLOW  # [workaround] see implementation
        )


@patch('stats.api_breakdowns.query')
class AdGroupBreakdownTestCase(TestCase):
    fixtures = ['test_api', 'test_views', 'test_non_superuser.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_permission(self, mock_query):
        url = reverse('breakdown_ad_groups', kwargs={
            'ad_group_id': 1,
            'breakdown': '/ad_group/dma/day'
        })

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    def test_post(self, mock_query):
        test_helper.add_permissions(
            self.user, ['can_access_table_breakdowns_feature_on_ad_group_level', 'can_view_breakdown_by_delivery'])

        mock_query.return_value = {}

        params = {
            'limit': 5,
            'offset': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': ['1', '3', '4'],
            'show_archived': 'true',
            'parents': ['1-2-33', '1-2-34', '1-3-22'],
        }

        response = self.client.post(
            reverse('breakdown_ad_groups', kwargs={
                'ad_group_id': 1,
                'breakdown': '/content_ad/source/dma/day'
            }),
            data=json.dumps({'params': params}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.AD_GROUPS,
            self.user,
            ['content_ad_id', 'source_id', 'dma', 'day'],
            {
                'allowed_content_ads': test_helper.QuerySetMatcher(models.ContentAd.objects.filter(ad_group_id=1)),
                'ad_group': models.AdGroup.objects.get(pk=1),
                'campaign': models.Campaign.objects.get(pk=1),
                'account': models.Account.objects.get(pk=1),
                'date__gte': datetime.date(2016, 1, 1),
                'date__lte': datetime.date(2016, 2, 3),
                'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
                'show_archived': True,
            },
            ANY,
            ['1-2-33', '1-2-34', '1-3-22'],
            '-clicks',
            33,
            5 + breakdown.REQUEST_LIMIT_OVERFLOW  # [workaround] see implementation
        )


class RequestOverflowTest(TestCase):
    def create_test_data(self):
        return [
            {
                'rows': [{}, {}, {}, {}, {}],
                'pagination': {
                    'offset': 0,
                    'limit': 5,
                    'count': -1,
                }
            }
        ]

    def test_complete_exact(self):
        self.assertEqual(breakdown._process_request_overflow(self.create_test_data(), 5, 1), [
            {
                'rows': [{}, {}, {}, {}, {}],
                'pagination': {
                    'offset': 0,
                    'limit': 5,
                    'count': 5,
                }
            }
        ])

    def test_complete_overflow(self):
        self.assertEqual(breakdown._process_request_overflow(self.create_test_data(), 4, 2), [
            {
                'rows': [{}, {}, {}, {}],
                'pagination': {
                    'offset': 0,
                    'limit': 4,
                    'count': 5,
                }
            }
        ])

    def test_complete_less(self):
        self.assertEqual(breakdown._process_request_overflow(self.create_test_data(), 10, 1), [
            {
                'rows': [{}, {}, {}, {}, {}],
                'pagination': {
                    'offset': 0,
                    'limit': 5,
                    'count': 5,
                }
            }
        ])

    def test_not_complete(self):
        self.assertEqual(breakdown._process_request_overflow(self.create_test_data(), 3, 2), [
            {
                'rows': [{}, {}, {}],
                'pagination': {
                    'offset': 0,
                    'limit': 3,
                    'count': -1,
                }
            }
        ])

    def test_next_page(self):
        rows = [{
            'rows': [{1}, {2}, {3}, {4}, {5}],
            'pagination': {
                'offset': 0,
                'limit': 5,
                'count': -1,
            }
        }]

        self.assertEqual(breakdown._process_request_overflow(rows, 4, 1), [{
            'rows': [{1}, {2}, {3}, {4}],
            'pagination': {
                'offset': 0,
                'limit': 4,
                'count': -1,
            }
        }])

        rows = [{
            'rows': [{5}, {6}, {7}],
            'pagination': {
                'offset': 0,
                'limit': 3,
                'count': 3,
            }
        }]

        self.assertEqual(breakdown._process_request_overflow(rows, 10, 1), [{
            'rows': [{5}, {6}, {7}],
            'pagination': {
                'offset': 0,
                'limit': 3,
                'count': 3,
            },
        }])


class LimitOffsetToPageTest(TestCase):

    def test_get_page_and_size(self):
        self.assertEquals(breakdown._get_page_and_size(0, 10), (1, 10))
        self.assertEquals(breakdown._get_page_and_size(10, 20), (1, 30))
        self.assertEquals(breakdown._get_page_and_size(30, 20), (1, 50))
        self.assertEquals(breakdown._get_page_and_size(50, 20), (1, 70))


class BreakdownHelperTest(TestCase):
    def test_add_performance_indicators(self):
        rows = [
            {'performance_campaign_goal_1': 1, 'ad_group_id': 1},
            {'performance_campaign_goal_2': 1, 'ad_group_id': 2},
        ]

        breakdown_helpers.format_report_rows_performance_fields(rows, Goals([], [], [], [], None))

        self.assertEquals(rows, [
            {'performance_campaign_goal_1': 1, 'ad_group_id': 1,
             'performance': {'list': [], 'overall': None}, 'styles': {}},
            {'performance_campaign_goal_2': 1, 'ad_group_id': 2,
             'performance': {'list': [], 'overall': None}, 'styles': {}},
        ])

    def test_dont_add_performance_indicators(self):
        rows = [
            {'ad_group_id': 1},
            {'ad_group_id': 2},
        ]

        breakdown_helpers.format_report_rows_performance_fields(rows, Goals([], [], [], [], None))

        self.assertEquals(rows, [
            {'ad_group_id': 1},
            {'ad_group_id': 2},
        ])

    def test_clean_non_relevant_fields(self):

        rows = [
            {'ad_group_id': 1, 'campaign_has_available_budget': 1, 'campaign_stop_inactive': False,
             'performance': {}, 'performance_campaign_goal_1': 1, },
            {'ad_group_id': 2, 'campaign_has_available_budget': 1, 'campaign_stop_inactive': False,
             'performance': {}, 'performance_campaign_goal_1': 1, },
        ]

        breakdown_helpers.clean_non_relevant_fields(rows)

        self.assertEquals(rows, [
            {'ad_group_id': 1, 'performance': {}},
            {'ad_group_id': 2, 'performance': {}},
        ])
