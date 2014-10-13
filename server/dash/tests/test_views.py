#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch, Mock
import datetime
import slugify

from django import test
from django import http
import xlrd

from dash import views


class AssertRowMixin(object):
    def _assert_row(self, worksheet, row_num, row_cell_list):
        for cell_num, cell_value in enumerate(row_cell_list):
            self.assertEqual(worksheet.cell_value(row_num, cell_num), cell_value)


class AdGroupExportBaseTestCase(AssertRowMixin, test.TestCase):

    def setUp(self):
        self.get_ad_group_patcher = patch('dash.views.get_ad_group')
        self.models_patcher = patch('dash.views.models')

        self.mock_get_ad_group = self.get_ad_group_patcher.start()
        self.mock_models = self.models_patcher.start()

        self.ad_group_id = 1
        self.ad_group_name = 'Test Ad Group'
        self.account_name = 'Test Account 1'

        self.mock_ad_group = Mock()
        self.mock_ad_group.id = self.ad_group_id
        self.mock_ad_group.name = self.ad_group_name
        self.mock_ad_group.campaign.account.name = self.account_name
        self.mock_get_ad_group.return_value = self.mock_ad_group

        self.mock_source1 = Mock()
        self.mock_source1.id = 1
        self.mock_source1.name = 'Test Source 1'

        self.mock_source2 = Mock()
        self.mock_source2.id = 2
        self.mock_source2.name = 'Test Source 2'

        self.mock_models.Source.objects.all.return_value = [self.mock_source1, self.mock_source2]

    def tearDown(self):
        self.get_ad_group_patcher.stop()
        self.models_patcher.stop()


class AdGroupAdsExportTestCase(AdGroupExportBaseTestCase):
    def setUp(self):
        super(AdGroupAdsExportTestCase, self).setUp()

        self.query_patcher = patch('dash.views.reports.api.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'article': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'title': u'Test Article with unicode Čžš',
                'url': 'http://www.example.com',
                'some_random_metric': '12'
            }],
            [{
                'article': 1,
                'source': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'title': u'Test Article with unicode Čžš',
                'url': 'http://www.example.com',
                'some_random_metric': '13'
            }]
        ]

    def tearDown(self):
        super(AdGroupAdsExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_csv(self):
        request = http.HttpRequest()
        request.GET['type'] = 'csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()

        response = views.AdGroupAdsExport().get(request, self.ad_group_id)

        expected_content = '''Date,Title,URL,Cost,CPC,Clicks,Impressions,CTR\r
2014-07-01,Test Article with unicode \xc4\x8c\xc5\xbe\xc5\xa1,http://www.example.com,1000.12,10.23,103,100000,1.03\r
'''

        filename = '{0}_{1}_detailed_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.ad_group_name)
        )

        self.assertEqual(
            response['Content-Type'],
            'text/csv; name="%s"' % filename
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )
        self.assertEqual(response.content, expected_content)

    def test_get_excel(self):
        request = http.HttpRequest()
        request.GET['type'] = 'excel'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()

        response = views.AdGroupAdsExport().get(request, self.ad_group_id)

        filename = '{0}_{1}_detailed_report_2014-06-30_2014-07-01.xlsx'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.ad_group_name)
        )

        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertEqual(
           response['Content-Disposition'],
           'attachment; filename="%s"' % filename
        )

        workbook = xlrd.open_workbook(file_contents=response.content)
        self.assertIsNotNone(workbook)

        worksheet = workbook.sheet_by_name('Detailed Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0, ['Date', 'Title', 'URL', 'Cost', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR'])

        self._assert_row(worksheet, 1, [41821.0, u'Test Article with unicode Čžš', 'http://www.example.com',
            1000.12, 10.23, 103, 100000, 0.0103])

        worksheet = workbook.sheet_by_name('Per Source Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0, ['Date', 'Title', 'URL', 'Source', 'Cost', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR'])

        self._assert_row(worksheet, 1, [41821.0, u'Test Article with unicode Čžš', 'http://www.example.com', 'Test Source 1',
            1000.12, 10.23, 103, 100000, 0.0103])


class AdGroupSourcesExportTestCase(AdGroupExportBaseTestCase):
    def setUp(self):
        super(AdGroupSourcesExportTestCase, self).setUp()

        self.query_patcher = patch('dash.views.reports.api.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'article': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': 12,
                'source': 2
            }],
            [{
                'article': 1,
                'source': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': 13,
                'source': 2
            }]
        ]

    def tearDown(self):
        super(AdGroupSourcesExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_csv(self):
        request = http.HttpRequest()
        request.GET['type'] = 'csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()

        response = views.AdGroupSourcesExport().get(request, self.ad_group_id)

        expected_content = '''Date,Source,Cost,CPC,Clicks,Impressions,CTR\r
2014-07-01,Test Source 2,1000.12,10.23,103,100000,1.03\r
'''

        filename = '{0}_{1}_per_sources_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.ad_group_name)
        )

        self.assertEqual(
            response['Content-Type'],
            'text/csv; name="%s"' % filename
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )
        self.assertEqual(response.content, expected_content)

    def test_get_excel(self):
        request = http.HttpRequest()
        request.GET['type'] = 'excel'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()

        response = views.AdGroupSourcesExport().get(request, self.ad_group_id)

        filename = '{0}_{1}_per_sources_report_2014-06-30_2014-07-01.xlsx'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.ad_group_name)
        )

        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertEqual(
           response['Content-Disposition'],
           'attachment; filename="%s"' % filename
        )

        workbook = xlrd.open_workbook(file_contents=response.content)
        self.assertIsNotNone(workbook)

        worksheet = workbook.sheet_by_name('Per Day Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0, ['Date', 'Cost', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR'])
        self._assert_row(worksheet, 1, [41821.0, 1000.12, 10.23, 103, 100000, 0.0103])

        worksheet = workbook.sheet_by_name('Per Source Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0, ['Date', 'Source', 'Cost', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR'])
        self._assert_row(worksheet, 1, [41821.0, 'Test Source 2', 1000.12, 10.23, 103, 100000, 0.0103])
