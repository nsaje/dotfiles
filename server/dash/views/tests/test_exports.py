#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch, Mock
import datetime
import slugify

from django import test
from django import http
import xlrd

from dash.views import export


class AssertRowMixin(object):
    def _assert_row(self, worksheet, row_num, row_cell_list):
        for cell_num, cell_value in enumerate(row_cell_list):
            self.assertEqual(worksheet.cell_value(row_num, cell_num), cell_value)


class AdGroupAdsPlusExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.ad_group_id = 1

        self.query_patcher = patch('dash.export.reports.api_contentads.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'content_ad': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': '12'
            }],
            [{
                'content_ad': 1,
                'source': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': '13'
            }]
        ]

        self.account_name = 'test account 1 Čžš'
        self.ad_group_name = 'test adgroup 1 Čžš'

    def tearDown(self):
        super(AdGroupAdsPlusExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_csv(self):
        request = http.HttpRequest()
        request.GET['type'] = 'csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()
        request.user.id = 1

        response = export.AdGroupAdsPlusExport().get(request, self.ad_group_id)

        expected_content = '''Date,Title,URL,Image URL,Cost,CPC,Clicks,Impressions,CTR\r\n2014-07-01,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,http://testurl.com,/123456789/200x300.jpg,1000.12,10.23,103,100000,1.03\r\n'''

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
        request.user.id = 1

        response = export.AdGroupAdsPlusExport().get(request, self.ad_group_id)

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

        self._assert_row(worksheet, 0, ['Date', 'Title', 'URL', 'Image URL', 'Cost', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR'])

        self._assert_row(worksheet, 1, [41821.0, u'Test Article unicode Čžš', 'http://testurl.com',
                                        '/123456789/200x300.jpg', 1000.12, 10.23, 103, 100000, 0.0103])

        worksheet = workbook.sheet_by_name('Per Source Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0, ['Date', 'Title', 'URL', 'Image URL', 'Source',
                                        'Cost', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR'])

        self._assert_row(worksheet, 1, [41821.0, u'Test Article unicode Čžš', 'http://testurl.com', '/123456789/200x300.jpg',
                                        'AdsNative', 1000.12, 10.23, 103, 100000, 0.0103])


class AdGroupAdsExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.ad_group_id = 1

        self.query_patcher = patch('dash.export.reports.api.query')
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
        self.account_name = 'test account 1 Čžš'
        self.ad_group_name = 'test adgroup 1 Čžš'

    def tearDown(self):
        super(AdGroupAdsExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_csv(self):
        request = http.HttpRequest()
        request.GET['type'] = 'csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()
        request.user.id = 1

        response = export.AdGroupAdsExport().get(request, self.ad_group_id)

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
        request.user.id = 1

        response = export.AdGroupAdsExport().get(request, self.ad_group_id)

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

        self._assert_row(worksheet, 1, [41821.0, u'Test Article with unicode Čžš', 'http://www.example.com', 'AdsNative',
            1000.12, 10.23, 103, 100000, 0.0103])


class AdGroupSourcesExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.ad_group_id = 1

        self.query_patcher = patch('dash.export.reports.api.query')
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
        self.account_name = 'test account 1 Čžš'
        self.ad_group_name = 'test adgroup 1 Čžš'

    def tearDown(self):
        super(AdGroupSourcesExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_csv(self):
        request = http.HttpRequest()
        request.GET['type'] = 'csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()
        request.user.id = 1

        response = export.AdGroupSourcesExport().get(request, self.ad_group_id)

        expected_content = '''Date,Source,Cost,CPC,Clicks,Impressions,CTR\r\n2014-07-01,Gravity,1000.12,10.23,103,100000,1.03\r\n'''

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
        request.user.id = 1

        response = export.AdGroupSourcesExport().get(request, self.ad_group_id)

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
        self._assert_row(worksheet, 1, [41821.0, 'Gravity', 1000.12, 10.23, 103, 100000, 0.0103])
