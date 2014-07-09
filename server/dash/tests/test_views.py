#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch, Mock
import datetime
import slugify

from django import test
from django import http
import xlrd

from dash import views


class AdGroupAdsExportTestCase(test.TestCase):

    def setUp(self):
        self.get_ad_group_patcher = patch('dash.views.get_ad_group')
        self.api_patcher = patch('dash.views.reports.api')
        self.models_patcher = patch('dash.views.models')

        self.mock_get_ad_group = self.get_ad_group_patcher.start()
        self.mock_api = self.api_patcher.start()
        self.mock_models = self.models_patcher.start()

        self.ad_group_id = 1
        self.ad_group_name = 'Test Ad Group'

        self.mock_ad_group = Mock()
        self.mock_ad_group.id = self.ad_group_id
        self.mock_ad_group.name = self.ad_group_name
        self.mock_get_ad_group.return_value = self.mock_ad_group

        self.mock_network1 = Mock()
        self.mock_network1.id = 1
        self.mock_network1.name = 'Test Network 1'

        self.mock_network2 = Mock()
        self.mock_network2.id = 2
        self.mock_network2.name = 'Test Network 2'

        self.mock_models.Network.objects.all.return_value = [self.mock_network1, self.mock_network2]

        self.mock_article = Mock()
        self.mock_article.id = 1
        self.mock_article.title = u'Test Article with unicode Čžš'
        self.mock_article.url = 'http://www.example.com'
        self.mock_models.Article.objects.filter.return_value = [self.mock_article]

        self.mock_api.query.side_effect = [
            [{
                'article': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.123242,
                'cpc': 10.2334,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.031231231
            }],
            [{
                'article': 1,
                'network': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.123242,
                'cpc': 10.2334,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.031231231
            }]
        ]


    def tearDown(self):
        self.get_ad_group_patcher.stop()
        self.api_patcher.stop()
        self.models_patcher.stop()


    def _assert_row(self, worksheet, row_num, row_cell_list):
        for cell_num, cell_value in enumerate(row_cell_list):
            self.assertEqual(worksheet.cell_value(row_num, cell_num), cell_value)


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

        filename = '%s_detailed_report_2014-06-30_2014-07-01.csv' % slugify.slugify(self.ad_group_name)

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

        filename = '%s_detailed_report_2014-06-30_2014-07-01.xls' % slugify.slugify(self.ad_group_name)

        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertEqual(
           response['Content-Disposition'],
           'attachment; filename="%s"' % filename
        )

        workbook = xlrd.open_workbook(file_contents=response.content)
        self.assertIsNotNone(workbook)

        worksheet = workbook.sheet_by_name('Detailed Report')
        self.assertIsNotNone(worksheet)


        self._assert_row(worksheet, 0, ['Date', 'Title', 'URL', 'Cost', 'CPC', 'Clicks', 'Impressions', 'CTR'])

        self._assert_row(worksheet, 1, [41821.0, u'Test Article with unicode Čžš', 'http://www.example.com',
            1000.123242, 10.2334, 103, 100000, 0.01031231231])

        worksheet = workbook.sheet_by_name('Per Network Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0, ['Date', 'Title', 'URL', 'Network', 'Cost', 'CPC', 'Clicks', 'Impressions', 'CTR'])

        self._assert_row(worksheet, 1, [41821.0, u'Test Article with unicode Čžš', 'http://www.example.com', 'Test Network 1',
            1000.123242, 10.2334, 103, 100000, 0.01031231231])
