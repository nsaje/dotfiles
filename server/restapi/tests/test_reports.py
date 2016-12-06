import datetime
import json
import mock

from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from zemauth.models import User

from dash import constants
import dash.models
import dash.threads
import restapi.models
from utils import test_helper
from restapi import reports


class ReportViewsTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.get(pk=1))

    @mock.patch('dash.threads.AsyncFunction', dash.threads.MockAsyncFunction)
    @mock.patch('restapi.reports.ReportJobExecutor', restapi.reports.MockJobExecutor)
    def test_new_job(self):
        query = {
            'fields': [{'field': 'Content Ad Id'}],
            'filters': [{'field': 'Ad Group Id', 'operator': '=', 'value': '123'},
                        {'field': 'Date', 'operator': '=', 'value': '2016-10-10'}]
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'IN_PROGRESS')
        self.assertIn('id', resp_json['data'])

        job_id = int(resp_json['data']['id'])
        job = restapi.models.ReportJob.objects.get(pk=job_id)
        job.status = constants.ReportJobStatus.DONE
        job.save()

        r = self.client.get(reverse('reports_details', kwargs={'job_id': job_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'DONE')
        self.assertEqual(job_id, int(resp_json['data']['id']))

    @mock.patch('dash.threads.AsyncFunction', dash.threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_raw_new_report_no_options(self, mock_prepare_constraints, mock_query, mock_totals):
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
            ad_group_ids=[1]
        )

        mock_query.assert_called_with(
            User.objects.get(pk=1),
            ['publisher_id'],
            mock.ANY,
            mock.ANY,
            '-e_media_cost'
        )

        self.assertFalse(mock_totals.called)

    @mock.patch('dash.threads.AsyncFunction', dash.threads.MockAsyncFunction)
    @mock.patch('stats.api_reports.totals', return_value={})
    @mock.patch('stats.api_reports.query', return_value=[])
    @mock.patch('stats.api_reports.prepare_constraints')
    def test_raw_new_report_form_handeled(self, mock_prepare_constraints, mock_query, mock_totals):
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
            ad_group_ids=[1]
        )

        mock_query.assert_called_with(
            User.objects.get(pk=1),
            ['publisher_id'],
            mock.ANY,
            mock.ANY,
            'clicks'
        )
        self.assertTrue(mock_totals.called)


class ReportsHeelpersTest(TestCase):

    @mock.patch('utils.dates_helper.local_today')
    def test_date_field_name_mapping(self, mock_today):
        mock_today.return_value = datetime.date(2016, 10, 12)
        self.assertDictEqual(reports.ReportJobExecutor._date_field_name_mapping({
            'status': 'Status',
            'publisher': 'Publisher',
            'clicks': 'Clicks',
        }), {
            'status': 'Status (2016-10-12)',
            'publisher': 'Publisher',
            'clicks': 'Clicks',
        })

    @mock.patch('utils.dates_helper.local_today')
    def test_date_fieldnames(self, mock_today):
        mock_today.return_value = datetime.date(2016, 10, 12)
        self.assertEqual(reports.ReportJobExecutor._date_fieldnames(['Status', 'Publisher', 'Clicks']), [
            'Status (2016-10-12)', 'Publisher', 'Clicks'
        ])
