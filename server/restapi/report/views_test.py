import datetime
import json
import mock

from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from zemauth.models import User

import dash.constants
import dash.models
from utils import test_helper, threads
from dash.features.reports import reports
from dash.features.reports import constants


class ReportViewsTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.get(pk=1))

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('dash.features.reports.reports.ReportJobExecutor', reports.MockJobExecutor)
    def test_new_job(self):
        query = {
            'fields': [{'field': 'Content Ad Id'}],
            'filters': [{'field': 'Ad Group Id', 'operator': '=', 'value': '1'},
                        {'field': 'Date', 'operator': '=', 'value': '2016-10-10'}]
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'IN_PROGRESS')
        self.assertIn('id', resp_json['data'])

        job_id = int(resp_json['data']['id'])
        job = dash.models.ReportJob.objects.get(pk=job_id)
        job.status = constants.ReportJobStatus.DONE
        job.save()

        r = self.client.get(reverse('reports_details', kwargs={'job_id': job_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'DONE')
        self.assertEqual(job_id, int(resp_json['data']['id']))

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_raw_new_report_no_options(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Publisher'}],
            'filters': [
                {'field': 'Ad Group Id', 'operator': '=', 'value': '1'},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['publisher_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            ad_group_ids=[1]
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['publisher_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='ad_groups',
            columns=['publisher'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_raw_new_report_batch(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        mock_query.side_effect = [[{}] * 10000, [{}] * 100]
        query = {
            'fields': [{'field': 'Publisher'}],
            'filters': [
                {'field': 'Ad Group Id', 'operator': '=', 'value': '1'},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['publisher_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            ad_group_ids=[1]
        )

        mock_query.assert_has_calls([mock.call(
            user=User.objects.get(pk=1),
            breakdown=['publisher_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='ad_groups',
            columns=['publisher'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        ), mock.call(
            user=User.objects.get(pk=1),
            breakdown=['publisher_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=10000,
            limit=10000,
            level='ad_groups',
            columns=['publisher'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )])

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_raw_new_report_form_handeled(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Publisher'}],
            'filters': [
                {'field': 'Ad Group Id', 'operator': '=', 'value': '1'},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
            'options': {
                'showArchived': True,
                'showBlacklistedPublishers': 'active',
                'includeTotals': True,
                'includeItemsWithNoSpend': True,
                'order': 'Clicks'
            }
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['publisher_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=True,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ACTIVE,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            ad_group_ids=[1]
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['publisher_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='clicks',
            offset=0,
            limit=10000,
            level='ad_groups',
            columns=['publisher'],
            include_items_with_no_spend=True,
            dashapi_cache={},
        )
        self.assertTrue(mock_totals.called)

    def test_get_report_job_authorization(self):
        query = {
            'fields': [{'field': 'Content Ad Id'}],
            'filters': [{'field': 'Ad Group Id', 'operator': '=', 'value': '1'},
                        {'field': 'Date', 'operator': '=', 'value': '2016-10-10'}]
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)

        job_id = int(resp_json['data']['id'])

        r = self.client.get(reverse('reports_details', kwargs={'job_id': job_id}))
        self.assertEqual(r.status_code, 200)

        # try as different user
        self.client.force_authenticate(user=User.objects.get(pk=2))
        r = self.client.get(reverse('reports_details', kwargs={'job_id': job_id}))
        self.assertEqual(r.status_code, 403)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_report_breakdown(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [
                {'field': 'Account'},
                {'field': 'Campaign Id'},
                {'field': 'Ad Group'},
                {'field': 'Content Ad Id'},
                {'field': 'Media Source'},
                {'field': 'Day'},
            ],
            'filters': [
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['account_id', 'campaign_id', 'ad_group_id', 'content_ad_id', 'source_id', 'day'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['account_id', 'campaign_id', 'ad_group_id', 'content_ad_id', 'source_id', 'day'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='all_accounts',
            columns=['account', 'campaign_id', 'ad_group', 'content_ad_id', 'source', 'day'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_report_all_account(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Account'}],
            'filters': [
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['account_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['account_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='all_accounts',
            columns=['account'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_report_account(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Campaign'}],
            'filters': [
                {'field': 'Account Id', 'operator': '=', 'value': '1'},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['campaign_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            account_ids=[1]
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['campaign_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='accounts',
            columns=['campaign'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_report_accounts(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Campaign'}],
            'filters': [
                {'field': 'Account Id', 'operator': 'IN', 'values': ['1', '2', '3']},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['campaign_id', 'account_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            account_ids=[1, 2, 3]
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['campaign_id', 'account_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='all_accounts',
            columns=['campaign'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_report_campaign(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Ad Group'}],
            'filters': [
                {'field': 'Campaign Id', 'operator': '=', 'value': '1'},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['ad_group_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            campaign_ids=[1]
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['ad_group_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='campaigns',
            columns=['ad_group'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_report_campaigns(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Ad Group'}],
            'filters': [
                {'field': 'Campaign Id', 'operator': 'IN', 'values': ['1', '2', '3']},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['ad_group_id', 'campaign_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            campaign_ids=[1, 2, 3]
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['ad_group_id', 'campaign_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='accounts',
            columns=['ad_group'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_report_ad_group(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Content Ad'}],
            'filters': [
                {'field': 'Ad Group Id', 'operator': '=', 'value': '1'},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['content_ad_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            ad_group_ids=[1]
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['content_ad_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='ad_groups',
            columns=['content_ad'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_report_ad_groups(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Content Ad'}],
            'filters': [
                {'field': 'Ad Group Id', 'operator': 'IN', 'values': ['1', '2', '3']},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['content_ad_id', 'ad_group_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            ad_group_ids=[1, 2, 3]
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['content_ad_id', 'ad_group_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='campaigns',
            columns=['content_ad'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('utils.threads.AsyncFunction', threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.get_filename', return_value='')
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_report_content_ads(self, mock_prepare_constraints, mock_query, mock_totals, mock_filename):
        query = {
            'fields': [{'field': 'Content Ad'}],
            'filters': [
                {'field': 'Content Ad Id', 'operator': 'IN', 'values': ['1', '2', '3']},
                {'field': 'Date', 'operator': '=', 'value': '2016-10-10'},
                {'field': 'Media Source', 'operator': 'IN', 'values': ['1']},
            ],
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)

        mock_prepare_constraints.assert_called_with(
            User.objects.get(pk=1),
            ['content_ad_id'],
            datetime.date(2016, 10, 10), datetime.date(2016, 10, 10),
            test_helper.QuerySetMatcher(dash.models.Source.objects.filter(pk__in=[1])),
            show_archived=False,
            show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL,
            only_used_sources=True,
            filtered_agencies=None,
            filtered_account_types=None,
            content_ad_ids=[1, 2, 3]
        )

        mock_query.assert_called_with(
            user=User.objects.get(pk=1),
            breakdown=['content_ad_id'],
            constraints=mock.ANY,
            goals=mock.ANY,
            order='-e_media_cost',
            offset=0,
            limit=10000,
            level='ad_groups',
            columns=['content_ad'],
            include_items_with_no_spend=False,
            dashapi_cache={},
        )

        self.assertFalse(mock_totals.called)


class ReportsHeelpersTest(TestCase):

    @mock.patch('utils.dates_helper.local_today')
    def test_date_column_names(self, mock_today):
        mock_today.return_value = datetime.date(2016, 10, 12)
        self.assertEqual(reports.ReportJobExecutor._date_column_names(['Status', 'Publisher', 'Clicks']), ([
            'Status (2016-10-12)', 'Publisher', 'Clicks'
        ], {
            'Status': 'Status (2016-10-12)', 'Publisher': 'Publisher', 'Clicks': 'Clicks'
        }))
