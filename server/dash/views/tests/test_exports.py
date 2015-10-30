#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
from mock import patch, Mock
import datetime
import slugify

from django import test
from django import http
from django.conf import settings
import xlrd

from dash.views import export
import dash.models

from zemauth import models
from utils import exc


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
                'visits': 40,
                'click_discrepancy': 0.2,
                'pageviews': 123,
                'percent_new_users': 33.0,
                'bounce_rate': 12.0,
                'pv_per_visit': 0.9,
                'avg_tos': 1.0,
                'some_random_metric': '12'
            }, {
                'content_ad': 2,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 20.23,
                'clicks': 203,
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
        self.campaign = 'test campaign 1 Čžš'
        self.ad_group_name = 'test adgroup 1 Čžš'

    def tearDown(self):
        super(AdGroupAdsPlusExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_view(self):
        request = http.HttpRequest()
        request.GET['type'] = 'view-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,visits'
        request.GET['order'] = '-visits'
        request.user = Mock()
        request.user.id = 1

        response = export.AdGroupAdsPlusExport().get(request, self.ad_group_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,Average CPC,Clicks,Visits\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789/200x300.jpg,10.23,103,40\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article with no content_ad_sources 1,/123456789/200x300.jpg,20.23,203,30\r\n'''
        filename = '{0}_{1}_{2}_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.campaign),
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


class CampaignAdGroupsExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.campaign_id = 1
        self.query_patcher = patch('dash.export.reports.api.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'content_ad': 1,
                'ad_group': 1,
                'campaign': 1,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03
            }, {
                'content_ad': 2,
                'ad_group': 2,
                'campaign': 1,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 2000.12,
                'cpc': 20.23,
                'clicks': 203,
                'impressions': 200000,
                'ctr': 2.03
            }]
        ]

        self.account_name = 'test account 1 Čžš'
        self.campaign_name = 'test campaign 1 Čžš'

    def tearDown(self):
        super(CampaignAdGroupsExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_view(self):
        request = http.HttpRequest()
        request.GET['type'] = 'view-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = 'impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.CampaignAdGroupsExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,10.23,103,100000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,test adgroup 2,20.23,203,200000\r\n'''

        filename = '{0}_{1}_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.campaign_name)
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

    def test_get_by_content_ad(self):
        request = http.HttpRequest()
        request.GET['type'] = 'contentad-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = 'impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.CampaignAdGroupsExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789/200x300.jpg,10.23,103,100000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article with no content_ad_sources 1,/123456789/200x300.jpg,20.23,203,200000\r\n'''

        filename = '{0}_{1}_-_by_content_ad_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.campaign_name)
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


class AccountCampaignsExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.account_id = 1
        self.query_patcher = patch('dash.export.reports.api.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'content_ad': 1,
                'ad_group': 1,
                'campaign': 1,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03
            }, {
                'content_ad': 2,
                'ad_group': 2,
                'campaign': 2,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 2000.12,
                'cpc': 20.23,
                'clicks': 203,
                'impressions': 200000,
                'ctr': 2.03
            }]
        ]

        self.account_name = 'test account 1 Čžš'

    def tearDown(self):
        super(AccountCampaignsExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_view(self):
        request = http.HttpRequest()
        request.GET['type'] = 'view-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = 'impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.AccountCampaignsExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,10.23,103,100000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,20.23,203,200000\r\n'''

        filename = '{0}_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name)
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

    def test_get_by_ad_group(self):
        request = http.HttpRequest()
        request.GET['type'] = 'adgroup-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)
        request.GET['order'] = 'impressions'

        response = export.AccountCampaignsExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,10.23,103,100000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,test adgroup 2,20.23,203,200000\r\n'''

        filename = '{0}_-_by_ad_group_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name)
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

    def test_get_by_content_ad(self):
        request = http.HttpRequest()
        request.GET['type'] = 'contentad-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)
        request.GET['order'] = 'impressions'

        response = export.AccountCampaignsExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789/200x300.jpg,10.23,103,100000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article with no content_ad_sources 1,/123456789/200x300.jpg,20.23,203,200000\r\n'''

        filename = '{0}_-_by_content_ad_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name)
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


class AllAccountsExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.query_patcher = patch('dash.export.reports.api.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'content_ad': 1,
                'ad_group': 1,
                'campaign': 1,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03
            }, {
                'content_ad': 2,
                'ad_group': 2,
                'campaign': 2,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 2000.12,
                'cpc': 20.23,
                'clicks': 203,
                'impressions': 200000,
                'ctr': 2.03
            }]
        ]

    def tearDown(self):
        super(AllAccountsExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_view(self):
        request = http.HttpRequest()
        request.GET['type'] = 'view-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.AllAccountsExport().get(request)

        expected_content = '''Start Date,End Date,Account,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,20.23,203,200000\r\n'''

        filename = 'ZemantaOne_report_2014-06-30_2014-07-01.csv'

        self.assertEqual(
            response['Content-Type'],
            'text/csv; name="%s"' % filename
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )
        self.assertEqual(response.content, expected_content)

    def test_get_by_campaign(self):
        request = http.HttpRequest()
        request.GET['type'] = 'campaign-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)
        request.GET['order'] = '-impressions'

        response = export.AllAccountsExport().get(request)

        expected_content = '''Start Date,End Date,Account,Campaign,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,20.23,203,200000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,10.23,103,100000\r\n'''

        filename = 'ZemantaOne_-_by_campaign_report_2014-06-30_2014-07-01.csv'

        self.assertEqual(
            response['Content-Type'],
            'text/csv; name="%s"' % filename
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )
        self.assertEqual(response.content, expected_content)

    def test_get_by_ad_group(self):
        request = http.HttpRequest()
        request.GET['type'] = 'adgroup-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)
        request.GET['order'] = 'impressions'

        response = export.AllAccountsExport().get(request)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,10.23,103,100000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,test adgroup 2,20.23,203,200000\r\n'''

        filename = 'ZemantaOne_-_by_ad_group_report_2014-06-30_2014-07-01.csv'

        self.assertEqual(
            response['Content-Type'],
            'text/csv; name="%s"' % filename
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )
        self.assertEqual(response.content, expected_content)


class AdGroupSourcesExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.ad_group_id = 1

        self.query_patcher = patch('dash.export.reports.api.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'content_ad': 1,
                'ad_group': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': 12,
                'source': 4
            }, {
                'content_ad': 2,
                'ad_group': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 20.23,
                'clicks': 203,
                'impressions': 200000,
                'ctr': 1.03,
                'some_random_metric': 13,
                'source': 1
            }]
        ]
        self.account_name = 'test account 1 Čžš'
        self.campaign_name = 'test campaign 1 Čžš'
        self.ad_group_name = 'test adgroup 1 Čžš'

    def tearDown(self):
        super(AdGroupSourcesExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_view(self):
        request = http.HttpRequest()
        request.GET['type'] = 'view-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = '-impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.AdGroupSourcesExport().get(request, self.ad_group_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,AdsNative,20.23,203,200000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Taboola,10.23,103,100000\r\n'''

        filename = '{0}_{1}_{2}_media_source_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.campaign_name),
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


class CampaignSourcesExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.campaign_id = 1

        self.query_patcher = patch('dash.export.reports.api.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'content_ad': 1,
                'ad_group': 1,
                'campaign': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': 12,
                'source': 4
            }]
        ]
        self.account_name = 'test account 1 Čžš'
        self.campaign_name = 'test campaign 1 Čžš'

    def tearDown(self):
        super(CampaignSourcesExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_view(self):
        request = http.HttpRequest()
        request.GET['type'] = 'view-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.CampaignSourcesExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,Taboola,10.23,103,100000\r\n'''

        filename = '{0}_{1}_media_source_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.campaign_name)
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

    def test_get_by_ad_group(self):
        request = http.HttpRequest()
        request.GET['type'] = 'adgroup-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.CampaignSourcesExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Taboola,10.23,103,100000\r\n'''

        filename = '{0}_{1}_-_by_ad_group_media_source_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.campaign_name)
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

    def test_get_by_content_ad(self):
        request = http.HttpRequest()
        request.GET['type'] = 'contentad-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.CampaignSourcesExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789/200x300.jpg,Taboola,10.23,103,100000\r\n'''

        filename = '{0}_{1}_-_by_content_ad_media_source_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name),
            slugify.slugify(self.campaign_name)
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


class AccountSourcesExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.account_id = 1

        self.query_patcher = patch('dash.export.reports.api.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'content_ad': 1,
                'ad_group': 1,
                'campaign': 1,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': 12,
                'source': 4
            }]
        ]
        self.account_name = 'test account 1 Čžš'

    def tearDown(self):
        super(AccountSourcesExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_view(self):
        request = http.HttpRequest()
        request.GET['type'] = 'view-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.AccountSourcesExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,Taboola,10.23,103,100000\r\n'''

        filename = '{0}_media_source_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name)
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

    def test_get_by_campaign(self):
        request = http.HttpRequest()
        request.GET['type'] = 'campaign-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.AccountSourcesExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,Taboola,10.23,103,100000\r\n'''

        filename = '{0}_-_by_campaign_media_source_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name)
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

    def test_get_by_ad_group(self):
        request = http.HttpRequest()
        request.GET['type'] = 'adgroup-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.AccountSourcesExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Taboola,10.23,103,100000\r\n'''

        filename = '{0}_-_by_ad_group_media_source_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name)
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

    def test_get_by_content_ad(self):
        request = http.HttpRequest()
        request.GET['type'] = 'contentad-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.AccountSourcesExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789/200x300.jpg,Taboola,10.23,103,100000\r\n'''

        filename = '{0}_-_by_content_ad_media_source_report_2014-06-30_2014-07-01.csv'.format(
            slugify.slugify(self.account_name)
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


class AllAccountsSourcesExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.query_patcher = patch('dash.export.reports.api.query')
        self.mock_query = self.query_patcher.start()
        self.mock_query.side_effect = [
            [{
                'ad_group': 1,
                'campaign': 1,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'cpc': 10.23,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': 12,
                'source': 4
            }, {
                'ad_group': 2,
                'campaign': 2,
                'account': 1,
                'date': datetime.date(2014, 7, 1),
                'cost': 2000.12,
                'cpc': 20.23,
                'clicks': 203,
                'impressions': 200000,
                'ctr': 2.03,
                'some_random_metric': 13,
                'source': 3
            }]
        ]

    def tearDown(self):
        super(AllAccountsSourcesExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_view(self):
        request = http.HttpRequest()
        request.GET['type'] = 'view-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = '-impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.AllAccountsSourcesExport().get(request)

        expected_content = '''Start Date,End Date,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,Outbrain,20.23,203,200000\r
2014-06-30,2014-07-01,Taboola,10.23,103,100000\r\n'''

        filename = 'ZemantaOne_media_source_report_2014-06-30_2014-07-01.csv'

        self.assertEqual(
            response['Content-Type'],
            'text/csv; name="%s"' % filename
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )
        self.assertEqual(response.content, expected_content)

    def test_get_by_account(self):
        request = http.HttpRequest()
        request.GET['type'] = 'account-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)
        request.GET['order'] = '-impressions'

        response = export.AllAccountsSourcesExport().get(request)

        expected_content = '''Start Date,End Date,Account,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,Outbrain,20.23,203,200000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,Taboola,10.23,103,100000\r\n'''

        filename = 'ZemantaOne_-_by_account_media_source_report_2014-06-30_2014-07-01.csv'

        self.assertEqual(
            response['Content-Type'],
            'text/csv; name="%s"' % filename
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )
        self.assertEqual(response.content, expected_content)

    def test_get_by_campaign(self):
        request = http.HttpRequest()
        request.GET['type'] = 'campaign-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)
        request.GET['order'] = '-impressions'

        response = export.AllAccountsSourcesExport().get(request)

        expected_content = '''Start Date,End Date,Account,Campaign,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,Outbrain,20.23,203,200000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,Taboola,10.23,103,100000\r\n'''

        filename = 'ZemantaOne_-_by_campaign_media_source_report_2014-06-30_2014-07-01.csv'

        self.assertEqual(
            response['Content-Type'],
            'text/csv; name="%s"' % filename
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )
        self.assertEqual(response.content, expected_content)

    def test_get_by_ad_group(self):
        request = http.HttpRequest()
        request.GET['type'] = 'adgroup-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = '-impressions'
        request.user = models.User.objects.get(pk=2)

        response = export.AllAccountsSourcesExport().get(request)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Source,Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,test adgroup 2,Outbrain,20.23,203,200000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Taboola,10.23,103,100000\r\n'''

        filename = 'ZemantaOne_-_by_ad_group_media_source_report_2014-06-30_2014-07-01.csv'

        self.assertEqual(
            response['Content-Type'],
            'text/csv; name="%s"' % filename
        )
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="%s"' % filename
        )
        self.assertEqual(response.content, expected_content)
