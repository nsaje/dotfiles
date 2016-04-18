#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
from mock import patch, Mock
import datetime
import slugify

from django import test
from django import http
import xlrd

from dash.views import export
import dash.models

from zemauth import models


class AssertRowMixin(object):
    def _assert_row(self, worksheet, row_num, row_cell_list):
        for cell_num, cell_value in enumerate(row_cell_list):
            self.assertEqual(worksheet.cell_value(row_num, cell_num), cell_value)


class AllAccountsExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.query_patcher = patch('dash.export.reports.api_contentads.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'account': 1,
                'campaign': 1,
                'content_ad': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'visits': 40,
                'click_discrepancy': 0.2,
                'pageviews': 123,
                'percent_new_users': 33.0,
                'bounce_rate': 12.0,
                'pv_per_visit': 0.9,
                'avg_tos': 1.0,
                'some_random_metric': '12'
            }],
            [{
                'account': 1,
                'campaign': 1,
                'content_ad': 1,
                'source': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'visits': 30,
                'click_discrepancy': 0.1,
                'pageviews': 122,
                'percent_new_users': 32.0,
                'bounce_rate': 11.0,
                'pv_per_visit': 0.8,
                'avg_tos': 0.9,
                'some_random_metric': '13'
            }]
        ]

    def tearDown(self):
        super(AllAccountsExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_detailed_report_excel(self):
        request = http.HttpRequest()
        request.GET['type'] = 'excel'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()
        request.user.id = 1

        response = export.AllAccountsExport().get(request)

        filename = 'all_accounts_report_2014-06-30_2014-07-01.xlsx'

        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )

        workbook = xlrd.open_workbook(file_contents=response.content)
        self.assertIsNotNone(workbook)

        worksheet = workbook.sheet_by_name('Detailed Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(
            worksheet, 4,
            ['Date', 'Account', 'Campaign', 'Campaign Manager', 'Sales Representative',
             'Service Fee', 'IAB Category', 'Promotion Goal', 'Spend', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR',
             'Fee Amount', 'Total Amount']
        )

        service_fee = 0.2
        cost = 1000.12
        fee_amount = round((cost / (1.0 - service_fee)) - cost, ndigits=2)
        total_amount = fee_amount + cost

        self._assert_row(
            worksheet, 5,
            [41821.0, u'test account 1 \u010c\u017e\u0161', u'test campaign 1 \u010c\u017e\u0161', 'N/A', 'N/A',
             service_fee, 'N/A', 'N/A', cost, 10.23, 103.0, 100000.0, 0.0103,
             fee_amount, total_amount]
        )

    def test_add_campaign_data(self):
        request = http.HttpRequest()
        request.user = models.User.objects.get(pk=2)

        results = [{
            'account': 1
        }]
        accounts = dash.models.Account.objects.filter(pk=1)

        account = accounts[0]
        account_settings = account.get_current_settings()
        account_settings.service_fee = 0.13
        account_settings.save(request)

        export.AllAccountsExport().add_account_data(results, accounts)

        self.assertItemsEqual(results, [{
            'account': account.name,
            'service_fee': 0.13
        }])

        results[0].update({
            'campaign': 1,
            'cost': 957.97
        })

        results_copy = copy.copy(results)
        export.AllAccountsExport().add_campaign_data(results_copy, accounts)

        self.assertItemsEqual(results_copy, [{
            'account': u'test account 1 \u010c\u017e\u0161',
            'iab_category': 'N/A',
            'total_amount': 1101.1149425287356,
            'campaign': u'test campaign 1 \u010c\u017e\u0161',
            'fee_amount': 143.14494252873556,
            'campaign_manager': 'N/A',
            'promotion_goal': 'N/A',
            'cost': 957.97,
            'service_fee': 0.13,
            'sales_representative': 'N/A'
        }])

        results[0].update({
            'campaign': 1,
            'cost': 957.97,
            'service_fee': 'N/A'
        })

        results_copy = copy.copy(results)
        export.AllAccountsExport().add_campaign_data(results_copy, accounts)

        self.assertItemsEqual(results_copy, [{
            'account': u'test account 1 \u010c\u017e\u0161',
            'iab_category': 'N/A',
            'total_amount': 'N/A',
            'campaign': u'test campaign 1 \u010c\u017e\u0161',
            'fee_amount': 'N/A',
            'campaign_manager': 'N/A',
            'promotion_goal': 'N/A',
            'cost': 957.97,
            'service_fee': 'N/A',
            'sales_representative': 'N/A'
        }])


class AdGroupAdsExportTestCase(AssertRowMixin, test.TestCase):
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
                'visits': 40,
                'click_discrepancy': 0.2,
                'pageviews': 123,
                'percent_new_users': 33.0,
                'bounce_rate': 12.0,
                'pv_per_visit': 0.9,
                'avg_tos': 1.0,
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
                'visits': 30,
                'click_discrepancy': 0.1,
                'pageviews': 122,
                'percent_new_users': 32.0,
                'bounce_rate': 11.0,
                'pv_per_visit': 0.8,
                'avg_tos': 0.9,
                'some_random_metric': '13'
            }]
        ]

        self.account_name = 'test account 1 Čžš'
        self.ad_group_name = 'test adgroup 1 Čžš'

    def tearDown(self):
        super(AdGroupAdsExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_day(self):
        request = http.HttpRequest()
        request.GET['type'] = 'day-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()
        request.user.id = 1

        response = export.AdGroupAdsExport().get(request, self.ad_group_id)

        expected_content = '''Date,Image URL,Title,URL,Uploaded,Spend,Avg. CPC,Clicks,Impressions,CTR,Visits,Click Discrepancy,Pageviews,% New Users,Bounce Rate,PV/Visit,Avg. ToS\r\n2014-07-01,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,http://testurl.com,2015-02-21,1000.12,10.23,103,100000,1.03,40,0.20,123,33.00,12.00,0.90,1.00\r\n'''

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

    def test_get_day_excel(self):
        request = http.HttpRequest()
        request.GET['type'] = 'day-excel'
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

        self._assert_row(
            worksheet, 0,
            ['Date', 'Image URL', 'Title', 'URL',
             'Uploaded', 'Spend', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR']
        )

        self._assert_row(
            worksheet, 1,
            [41821.0, '/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg', u'Test Article unicode Čžš', 'http://testurl.com',
             42056.0, 1000.12, 10.23, 103, 100000, 0.0103]
        )

        worksheet = workbook.sheet_by_name('Per Source Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0,
            ['Date', 'Image URL', 'Title', 'URL', 'Uploaded', 'Source',
             'Spend', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR']
        )

        self._assert_row(
            worksheet, 1,
            [41821.0, '/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg', u'Test Article unicode Čžš', 'http://testurl.com',
            42056.0, 'AdsNative', 1000.12, 10.23, 103, 100000, 0.0103]
        )

    def test_get_content_ad(self):
        request = http.HttpRequest()
        request.GET['type'] = 'content-ad-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.user = Mock()
        request.user.id = 1

        response = export.AdGroupAdsExport().get(request, self.ad_group_id)

        expected_content = '''Image URL,Title,URL,Uploaded,Spend,Avg. CPC,Clicks,Impressions,CTR,Visits,Click Discrepancy,Pageviews,% New Users,Bounce Rate,PV/Visit,Avg. ToS\r\n/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,http://testurl.com,2015-02-21,1000.12,10.23,103,100000,1.03,40,0.20,123,33.00,12.00,0.90,1.00\r\n'''

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

    def test_get_content_ad_excel(self):
        request = http.HttpRequest()
        request.GET['type'] = 'content-ad-excel'
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

        self._assert_row(
            worksheet, 0,
            ['Image URL', 'Title', 'URL',
             'Uploaded', 'Spend', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR']
        )

        self._assert_row(
            worksheet, 1,
            ['/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg', u'Test Article unicode Čžš', 'http://testurl.com',
             42056.0, 1000.12, 10.23, 103, 100000, 0.0103]
        )

        worksheet = workbook.sheet_by_name('Per Source Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0,
            ['Image URL', 'Title', 'URL', 'Uploaded', 'Source',
             'Spend', 'Avg. CPC', 'Clicks', 'Impressions', 'CTR']
        )

        self._assert_row(
            worksheet, 1,
            ['/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg', u'Test Article unicode Čžš', 'http://testurl.com',
            42056.0, 'AdsNative', 1000.12, 10.23, 103, 100000, 0.0103]
        )


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
        request.user = models.User.objects.get(pk=2)

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
        request.user = models.User.objects.get(pk=2)

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
