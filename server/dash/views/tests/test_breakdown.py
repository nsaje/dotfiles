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

    @patch('stats.api_breakdowns.totals')
    def test_post_base_level(self, mock_totals, mock_query):
        test_helper.add_permissions(self.user, ['can_access_table_breakdowns_feature', 'all_accounts_accounts_view'])

        mock_totals.return_value = {
            'ctr': 0.9,
            'clicks': 123,
        }

        mock_query.return_value = [{
            'account_id': 116,
            'account_type': u'Self-managed',
            'agency': u'MBuy',
            'archived': False,
            'breakdown_id': u'116',
            'breakdown_name': u"Cat's Pride",
            'click_discrepancy': None,
            'ctr': 0.682212242285772,
            'default_account_manager': u'Helen Wagner',
            'default_sales_representative': u'David Kaplan',
            'impressions': 9484585,
            'name': "Cat's Pride",
            'parent_breakdown_id': None,
            'pv_per_visit': None,
            'status': 1,
        }, {
            'account_id': 305,
            'account_type': u'Pilot',
            'agency': '',
            'archived': False,
            'breakdown_id': u'305',
            'breakdown_name': u'Outbrain',
            'click_discrepancy': None,
            'ctr': 0.445301342321372,
            'default_account_manager': u'Tadej Pavli\u010d',
            'default_sales_representative': u'David Kaplan',
            'impressions': 13136273,
            'name': 'Outbrain',
            'parent_breakdown_id': None,
            'pv_per_visit': None,
            'status': 1,
        }]

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

        self.assertDictEqual(result, {
            'success': True,
            'data': [{
                'breakdown_id': None,
                'conversion_goals': [],
                'pixels': [],
                'pagination': {
                    'count': 3,
                    'limit': 2,
                    'offset': 1,
                },
                'rows': [{
                    'account_id': 116,
                    'account_type': u'Self-managed',
                    'agency': u'MBuy',
                    'archived': False,
                    'breakdown_id': u'116',
                    'breakdown_name': u"Cat's Pride",
                    'click_discrepancy': None,
                    'ctr': 0.682212242285772,
                    'default_account_manager': u'Helen Wagner',
                    'default_sales_representative': u'David Kaplan',
                    'impressions': 9484585,
                    'name': u"Cat's Pride",
                    'parent_breakdown_id': None,
                    'pv_per_visit': None,
                    'status': {'value': 1},
                }, {
                    'account_id': 305,
                    'account_type': u'Pilot',
                    'agency': u'',
                    'archived': False,
                    'breakdown_id': u'305',
                    'breakdown_name': u'Outbrain',
                    'click_discrepancy': None,
                    'ctr': 0.445301342321372,
                    'default_account_manager': u'Tadej Pavli\u010d',
                    'default_sales_representative': u'David Kaplan',
                    'impressions': 13136273,
                    'name': u'Outbrain',
                    'parent_breakdown_id': None,
                    'pv_per_visit': None,
                    'status': {'value': 1},
                }],
                'totals': {
                    'ctr': 0.9,
                    'clicks': 123,
                }
            }],
        })


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

    @patch('stats.api_breakdowns.totals')
    def test_post_base_level(self, mock_totals, mock_query):
        test_helper.add_permissions(self.user, ['can_access_table_breakdowns_feature', 'account_campaigns_view'])

        mock_query.return_value = [{
            'campaign_id': 198,
            'breakdown_id': '198',
            'breakdown_name': 'Blog Campaign [Desktop]',
            'parent_breakdown_id': None,
            'archived': False,
            'campaign_manager': u'Ana Dejanovi\u0107',
            'cost': 9196.1064,
            'impressions': 9621740,
            'name': 'Blog Campaign [Desktop]',
            'pageviews': 78853,
            'status': 1,
        }, {
            'campaign_id': 413,
            'breakdown_id': '413',
            'breakdown_name': 'Learning Center',
            'parent_breakdown_id': None,
            'archived': False,
            'campaign_manager': u'Ana Dejanovi\u0107',
            'cost': 7726.1054,
            'impressions': 10441143,
            'name': u'Learning Center',
            'pageviews': 51896,
            'status': 1,
        }]

        mock_totals.return_value = {
            'clicks': 123,
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

        self.assertDictEqual(result, {
            'success': True,
            'data': [{
                'breakdown_id': None,
                'pagination': {
                    'count': 3,
                    'limit': 2,
                    'offset': 1,
                },
                'rows': [{
                    u'campaign_id': 198,
                    u'breakdown_id': u'198',
                    u'breakdown_name': u'Blog Campaign [Desktop]',
                    u'parent_breakdown_id': None,
                    u'archived': False,
                    u'campaign_manager': u'Ana Dejanovi\u0107',
                    u'cost': 9196.1064,
                    u'impressions': 9621740,
                    u'name': u'Blog Campaign [Desktop]',
                    u'pageviews': 78853,
                    u'status': {'value': 1},
                }, {
                    u'campaign_id': 413,
                    u'breakdown_id': u'413',
                    u'breakdown_name': u'Learning Center',
                    u'parent_breakdown_id': None,
                    u'archived': False,
                    u'campaign_manager': u'Ana Dejanovi\u0107',
                    u'cost': 7726.1054,
                    u'impressions': 10441143,
                    u'name': u'Learning Center',
                    u'pageviews': 51896,
                    u'status': {'value': 1},
                }],
                'totals': {
                    'clicks': 123,
                },
                'pixels': [{
                    'name': 'test',
                    'prefix': 'pixel_1',
                }],
                'conversion_goals': [
                    {'id': 'conversion_goal_2', 'name': 'test conversion goal 2'},
                    {'id': 'conversion_goal_3', 'name': 'test conversion goal 3'},
                    {'id': 'conversion_goal_4', 'name': 'test conversion goal 4'},
                    {'id': 'conversion_goal_5', 'name': 'test conversion goal 5'}
                ],
            }]
        })


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

    @patch('stats.api_breakdowns.totals')
    def test_post_base_level(self, mock_totals, mock_query):
        test_helper.add_permissions(
            self.user, ['can_access_table_breakdowns_feature_on_ad_group_level'])

        mock_query.return_value = {}

        mock_totals.return_value = {
            'clicks': 123,
        }

        params = {
            'limit': 5,
            'offset': 33,
            'order': '-clicks',
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': ['1', '3', '4'],
            'show_archived': 'true',
            'parents': [],
        }

        response = self.client.post(
            reverse('breakdown_ad_groups', kwargs={
                'ad_group_id': 1,
                'breakdown': '/content_ad'
            }),
            data=json.dumps({'params': params}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        mock_query.assert_called_with(
            Level.AD_GROUPS,
            self.user,
            ['content_ad_id'],
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
            [],
            '-clicks',
            33,
            5 + breakdown.REQUEST_LIMIT_OVERFLOW  # [workaround] see implementation
        )

        self.assertDictEqual(json.loads(response.content), {
            "data": [{
                "pagination": {"count": 33, "limit": 0, "offset": 33},
                "rows": {},
                "breakdown_id": None,
                "totals": {"clicks": 123},
                "batches": [
                    {"id": 2, "name": "Ich bin eine UploadBatch"},
                    {"id": 1, "name": "batch 1"}
                ],
                "conversion_goals": [
                    {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                    {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                    {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                    {"id": "conversion_goal_5", "name": "test conversion goal 5"}
                ],
                "pixels": [{"prefix": "pixel_1", "name": "test"}]}
            ],
            "success": True
        })


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

    fixtures = ['test_augmenter.yaml']

    def test_add_performance_indicators(self):
        rows = [
            {'performance_campaign_goal_1': 1, 'ad_group_id': 1, 'cpc': 0.2},
            {'performance_campaign_goal_2': 1, 'ad_group_id': 2},
        ]

        campaign_goals = models.CampaignGoal.objects.filter(pk__in=[1])
        breakdown_helpers.format_report_rows_performance_fields(rows, Goals(campaign_goals, [], [], [], []))

        self.assertEquals(rows, [
            {'performance_campaign_goal_1': 1, 'ad_group_id': 1, 'cpc': 0.2,
             'styles': {'cpc': 1}, 'performance': {
                 'list': [
                     {'emoticon': 1, 'text': '$0.200 CPC'}
                 ],
                 'overall': None
             }},
            {'performance_campaign_goal_2': 1, 'ad_group_id': 2,
             'performance': {'list': [{'emoticon': 2, 'text': 'N/A CPC'}],
                             'overall': None}, 'styles': {}},
        ])

    def test_dont_add_performance_indicators(self):
        rows = [
            {'ad_group_id': 1},
            {'ad_group_id': 2},
        ]

        breakdown_helpers.format_report_rows_performance_fields(rows, Goals([], [], [], [], []))

        self.assertEquals(rows, [
            {'ad_group_id': 1},
            {'ad_group_id': 2},
        ])

    def test_clean_non_relevant_fields(self):

        rows = [
            {'ad_group_id': 1, 'campaign_has_available_budget': 1, 'campaign_stop_inactive': False,
             'performance': {}, 'performance_campaign_goal_1': 1, 'status_per_source': 1},
            {'ad_group_id': 2, 'campaign_has_available_budget': 1, 'campaign_stop_inactive': False,
             'performance': {}, 'performance_campaign_goal_1': 1, },
        ]

        breakdown_helpers.clean_non_relevant_fields(rows)

        self.assertEquals(rows, [
            {'ad_group_id': 1, 'performance': {}},
            {'ad_group_id': 2, 'performance': {}},
        ])

    def test_content_ad_editable_rows(self):
        rows = [
            {'content_ad_id': 1, 'status_per_source': {
                1: {
                    'source_id': 1,
                    'source_name': 'Gravity',
                    'source_status': 1,
                    'submission_status': 1,
                    'submission_errors': None,
                },
                2: {
                    'source_id': 2,
                    'source_name': 'AdsNative',
                    'source_status': 2,
                    'submission_status': 2,
                    'submission_errors': 'Sumtingwoing',
                }
            }}
        ]

        breakdown_helpers.format_report_rows_content_ad_editable_fields(rows)

        self.assertEquals(rows, [{
            'content_ad_id': 1,
            'id': 1,
            'submission_status': [{
                'status': 1,
                'text': 'Pending',
                'name': 'Gravity',
                'source_state': ''
            }, {
                'status': 2,
                'text': 'Approved',
                'name': 'AdsNative',
                'source_state': '(paused)'
            }],
            'status_per_source': {  # this node gets removed in cleanup
                1: {
                    'source_id': 1,
                    'submission_status': 1,
                    'source_name': 'Gravity',
                    'source_status': 1,
                    'submission_errors': None
                },
                2: {
                    'source_id': 2,
                    'submission_status': 2,
                    'source_name': 'AdsNative',
                    'source_status': 2,
                    'submission_errors': 'Sumtingwoing'
                }
            },
            'editable_fields': {
                'state': {
                    'message': None,
                    'enabled': True
                }
            }
        }])
