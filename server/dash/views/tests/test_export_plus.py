#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
from mock import patch
import datetime
import slugify
import json
import time

from django import test
from django import http
from django.contrib.auth.models import Permission

from dash.views import export_plus
import dash.models
from dash import constants

from zemauth import models
from utils import exc
from utils import test_helper


class AssertRowMixin(object):
    def _assert_row(self, worksheet, row_num, row_cell_list):
        for cell_num, cell_value in enumerate(row_cell_list):
            self.assertEqual(worksheet.cell_value(row_num, cell_num), cell_value)


class AdGroupAdsExportTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.ad_group_id = 1

        self.query_patcher = patch('reports.api_contentads.query')
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
            }, {
                'content_ad': 3,
                'date': datetime.date(2014, 7, 1),
                'cost': 3000.12,
                'cpc': 30.23,
                'clicks': 303,
                'impressions': 300000,
                'ctr': 3.03,
                'visits': 20,
                'click_discrepancy': 0.3,
                'pageviews': 322,
                'percent_new_users': 33.0,
                'bounce_rate': 31.0,
                'pv_per_visit': 0.8,
                'avg_tos': 0.9,
                'some_random_metric': '14'
            }]
        ]

        self.account_name = 'test account 1 Čžš'
        self.campaign = 'test campaign 1 Čžš'
        self.ad_group_name = 'test adgroup 1 Čžš'

    def tearDown(self):
        super(AdGroupAdsExportTestCase, self).tearDown()
        self.query_patcher.stop()

    def test_get_content_ad(self):
        request = http.HttpRequest()
        request.GET['type'] = 'contentad-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,visits'
        request.GET['order'] = '-visits'
        request.user = models.User.objects.get(pk=1)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AdGroupAdsExport().get(request, self.ad_group_id)
        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,URL,Status (''' + time.strftime('%Y-%m-%d') + '''),Average CPC,Clicks,Visits\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,http://testurl.com,Active,10.230,103,40\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article with no content_ad_sources 1,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,http://testurl.com,Inactive,20.230,203,30\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article with no content_ad_sources 2,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,http://testurl.com,Archived,30.230,303,20\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)
        filename = '{0}_{1}_{2}_-_by_content_ad_report_2014-06-30_2014-07-01.csv'.format(
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
        self.query_patcher = patch('reports.api.query')
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

    def test_get_ad_group(self):
        request = http.HttpRequest()
        request.GET['type'] = 'adgroup-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = 'impressions'
        request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.CampaignAdGroupsExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Status (''' + time.strftime('%Y-%m-%d') + '''),Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,10.230,103,100000\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,test adgroup 2,Inactive,20.230,203,200000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

        filename = '{0}_{1}_-_by_ad_group_report_2014-06-30_2014-07-01.csv'.format(
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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.CampaignAdGroupsExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,URL,Status (''' + time.strftime('%Y-%m-%d') + '''),Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,http://testurl.com,Active,10.230,103,100000\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article with no content_ad_sources 1,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,http://testurl.com,Inactive,20.230,203,200000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        self.query_patcher = patch('reports.api.query')
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

    def test_get_by_campaign(self):
        request = http.HttpRequest()
        request.GET['type'] = 'campaign-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = 'impressions'
        request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AccountCampaignsExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Status (''' + time.strftime('%Y-%m-%d') + '''),Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,10.230,103,100000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,Inactive,20.230,203,200000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

        '\xef\xbb\xbf"Start Date","End Date","Account","Campaign","Status (2016-03-23)","Average CPC","Clicks","Impressions"\r\n"2014-06-30","2014-07-01","test account 1 \xc4\x8c\xc5\xbe\xc5\xa1","test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1","Inactive","10.230","103","100000"\r\n"2014-06-30","2014-07-01","test account 1 \xc4\x8c\xc5\xbe\xc5\xa1","test campaign 2","Inactive","20.230","203","200000"\r\n'\
        '\xef\xbb\xbf"Start Date","End Date","Account","Campaign","Status (2016-03-23)","Average CPC","Clicks","Impressions"\r\n"2014-06-30","2014-07-01","test account 1 \xc4\x8c\xc5\xbe\xc5\xa1","test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1","Inactive","10.230","103","100000"\r\n"2014-06-30","2014-07-01","test account 1 \xc4\x8c\xc5\xbe\xc5\xa1","test campaign 2","Inactive","20.230","203","200000"\r\n""'
        filename = '{0}_-_by_campaign_report_2014-06-30_2014-07-01.csv'.format(
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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)
        request.GET['order'] = 'impressions'

        response = export_plus.AccountCampaignsExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Status (''' + time.strftime('%Y-%m-%d') + '''),Average CPC,Clicks,Impressions\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,10.230,103,100000\r
2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,test adgroup 2,Inactive,20.230,203,200000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)
        request.GET['order'] = 'impressions'

        response = export_plus.AccountCampaignsExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,URL,Status (''' + time.strftime('%Y-%m-%d') + '''),Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,http://testurl.com,Active,10.230,103,100000\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article with no content_ad_sources 1,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,http://testurl.com,Inactive,20.230,203,200000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        self.query_patcher = patch('reports.api.query')
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

    def test_get_by_account(self):
        request = http.HttpRequest()
        request.GET['type'] = 'account-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AllAccountsExport().get(request)

        expected_content = '''Start Date,End Date,Account,Status (''' + time.strftime('%Y-%m-%d') + '''),Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,20.230,203,200000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

        filename = 'ZemantaOne_-_by_account_report_2014-06-30_2014-07-01.csv'

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)
        request.GET['order'] = '-impressions'

        response = export_plus.AllAccountsExport().get(request)

        expected_content = '''Start Date,End Date,Account,Campaign,Status (''' + time.strftime('%Y-%m-%d') + '''),Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,Inactive,20.230,203,200000\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)
        request.GET['order'] = 'impressions'

        response = export_plus.AllAccountsExport().get(request)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Status (''' + time.strftime('%Y-%m-%d') + '''),Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,10.230,103,100000\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,test adgroup 2,Inactive,20.230,203,200000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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

        self.query_patcher = patch('reports.api.query')
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

    def test_get_by_adgroup(self):
        request = http.HttpRequest()
        request.GET['type'] = 'adgroup-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = '-impressions'
        request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AdGroupSourcesExport().get(request, self.ad_group_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Active,AdsNative,20.230,203,200000\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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

        self.query_patcher = patch('reports.api.query')
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

    def test_get_by_campaign(self):
        request = http.HttpRequest()
        request.GET['type'] = 'campaign-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.CampaignSourcesExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.CampaignSourcesExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.CampaignSourcesExport().get(request, self.campaign_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,URL,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,http://testurl.com,Active,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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

        self.query_patcher = patch('reports.api.query')
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

    def test_get_by_account(self):
        request = http.HttpRequest()
        request.GET['type'] = 'account-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AccountSourcesExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AccountSourcesExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AccountSourcesExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AccountSourcesExport().get(request, self.account_id)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Title,Image URL,URL,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789.jpg?w=200&h=300&fit=crop&crop=faces&fm=jpg,http://testurl.com,Active,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        self.query_patcher = patch('reports.api.query')
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

    def test_get_all_accounts(self):
        request = http.HttpRequest()
        request.GET['type'] = 'allaccounts-csv'
        request.GET['start_date'] = '2014-06-30'
        request.GET['end_date'] = '2014-07-01'
        request.GET['additional_fields'] = 'cpc,clicks,impressions'
        request.GET['order'] = '-impressions'
        request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AllAccountsSourcesExport().get(request)

        expected_content = '''Start Date,End Date,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,Inactive,Outbrain,20.230,203,200000\r\n2014-06-30,2014-07-01,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)
        request.GET['order'] = '-impressions'

        response = export_plus.AllAccountsSourcesExport().get(request)

        expected_content = '''Start Date,End Date,Account,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Outbrain,20.230,203,200000\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)
        request.GET['order'] = '-impressions'

        response = export_plus.AllAccountsSourcesExport().get(request)

        expected_content = '''Start Date,End Date,Account,Campaign,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,,Outbrain,20.230,203,200000\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.AllAccountsSourcesExport().get(request)

        expected_content = '''Start Date,End Date,Account,Campaign,Ad Group,Status (''' + time.strftime('%Y-%m-%d') + '''),Source,Average CPC,Clicks,Impressions\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 2,test adgroup 2,,Outbrain,20.230,203,200000\r\n2014-06-30,2014-07-01,test account 1 \xc4\x8c\xc5\xbe\xc5\xa1,test campaign 1 \xc4\x8c\xc5\xbe\xc5\xa1,test adgroup 1 \xc4\x8c\xc5\xbe\xc5\xa1,Inactive,Taboola,10.230,103,100000\r\n'''
        expected_content = test_helper.format_csv_content(expected_content)

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


class ExportAllowedTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.request = http.HttpRequest()
        self.request.GET['start_date'] = '2014-06-30'
        self.request.GET['end_date'] = '2014-07-01'
        self.request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        self.request.user.user_permissions.add(permission)

    @patch('dash.views.export_plus.ExportAllowed.MAX_ROWS', 10000)
    def test_get_all_ok(self):
        with patch('dash.models.ContentAd') as p:
            p.objects.filter.return_value.count.return_value = 1
            response = export_plus.ExportAllowed().get(self.request, 'ad_groups', id_=1)
        expected = {
            'ad_group': True,
            'content_ad': True,
            'by_day': {
                'content_ad': True
            }
        }
        self.assertEqual(json.loads(response.content)['data'], expected)

    @patch('dash.views.export_plus.ExportAllowed.MAX_ROWS', 1)
    def test_get_too_many_rows(self):
        with patch('dash.models.ContentAd') as p:
            p.objects.filter.return_value.count.return_value = 1000
            response = export_plus.ExportAllowed().get(self.request, 'ad_groups', id_=1)
        expected = {
            'ad_group': True,
            'content_ad': False,
            'by_day': {
                'content_ad': False
            }
        }
        self.assertEqual(json.loads(response.content)['data'], expected)

    @patch('dash.views.export_plus.ExportAllowed.MAX_ROWS', 10000)
    @patch('dash.views.export_plus.ExportAllowed.ALL_ACC_BD_ADG_MAX_DAYS', 1)
    def test_get_too_many_days_breakdown(self):
        with patch('dash.models.ContentAd') as p:
            p.objects.filter.return_value.count.return_value = 1
            response = export_plus.ExportAllowed().get(self.request, 'all_accounts')
        expected = {
            'all_accounts': True,
            'account': True,
            'campaign': True,
            'ad_group': True,
            'by_day': {
                'ad_group': False,
                'campaign': True,
                'account': True
            }
        }
        self.assertEqual(json.loads(response.content)['data'], expected)


class SourcesExportAllowedTestCase(AssertRowMixin, test.TestCase):
    fixtures = ['test_api']

    def setUp(self):
        self.request = http.HttpRequest()
        self.request.GET['start_date'] = '2014-06-30'
        self.request.GET['end_date'] = '2014-07-01'
        self.request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        self.request.user.user_permissions.add(permission)

    @patch('dash.views.export_plus.SourcesExportAllowed.MAX_ROWS', 10000)
    def test_get_all_ok(self):
        with patch('dash.models.ContentAd') as p:
            p.objects.filter.return_value.count.return_value = 1
            response = export_plus.SourcesExportAllowed().get(self.request, 'ad_groups', id_=1)
        expected = {
            'ad_group': True,
            'content_ad': True,
            'by_day': {
                'ad_group': True,
                'content_ad': True
            }
        }
        self.assertEqual(json.loads(response.content)['data'], expected)

    @patch('dash.views.export_plus.SourcesExportAllowed.MAX_ROWS', 1)
    def test_get_too_many_rows(self):
        with patch('dash.models.ContentAd') as p:
            p.objects.filter.return_value.count.return_value = 1000
            response = export_plus.SourcesExportAllowed().get(self.request, 'ad_groups', id_=1)
        expected = {
            'ad_group': False,
            'content_ad': False,
            'by_day': {
                'ad_group': False,
                'content_ad': False
            }
        }
        self.assertEqual(json.loads(response.content)['data'], expected)

    @patch('dash.views.export_plus.SourcesExportAllowed.MAX_ROWS', 10000)
    @patch('dash.views.export_plus.SourcesExportAllowed.ALL_ACC_BD_ADG_MAX_DAYS', 1)
    def test_get_too_many_days_breakdown(self):
        with patch('dash.models.ContentAd') as p:
            p.objects.filter.return_value.count.return_value = 1
            response = export_plus.SourcesExportAllowed().get(self.request, 'all_accounts')
        expected = {
            'all_accounts': True,
            'account': True,
            'campaign': True,
            'ad_group': True,
            'by_day': {
                'ad_group': False,
                'campaign': True,
                'account': True,
                'all_accounts': True
            }
        }
        self.assertEqual(json.loads(response.content)['data'], expected)


class ScheduledReportsTest(test.TestCase):
    fixtures = ['test_api']

    def test_get(self):
        request = http.HttpRequest()
        request.user = models.User.objects.get(pk=1)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.ScheduledReports().get(request, 1)

        content = json.loads(response.content)

        self.assertEqual(content['data']['reports'], [{
            'name': 'Report 1',
            'recipients': 'test@zemanta.com',
            'level': u'Account - test account 1 \u010c\u017e\u0161',
            'scheduled_report_id': 1,
            'frequency': 'Daily',
            'granularity': 'Account'}])
        self.assertTrue(content['success'])

    def test_get_no_permission(self):
        request = http.HttpRequest()
        permission = Permission.objects.get(codename='exports_plus')
        request.user = models.User.objects.get(pk=2)
        request.user.user_permissions.add(permission)
        request.user.user_permissions.remove(permission)

        with self.assertRaises(exc.ForbiddenError):
            response = export_plus.ScheduledReports().get(request, 1)

    def test_get_scheduled_reports(self):
        request = http.HttpRequest()
        request.user = models.User.objects.get(pk=1)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        response = export_plus.ScheduledReports().get(request, 1)
        content = json.loads(response.content)
        self.assertEqual(len(content['data']['reports']), 1)

        request.user = models.User.objects.get(pk=2)
        request.user.user_permissions.add(permission)

        response = export_plus.ScheduledReports().get(request, 1)
        content = json.loads(response.content)
        self.assertEqual(len(content['data']['reports']), 0)

    def test_delete(self):
        request = http.HttpRequest()
        request.user = models.User.objects.get(pk=1)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        self.assertEqual(dash.models.ScheduledExportReport.objects.get(id=1).state, constants.ScheduledReportState.ACTIVE)

        response = export_plus.ScheduledReports().delete(request, 1)
        content = json.loads(response.content)
        self.assertTrue(content['success'])

        self.assertEqual(dash.models.ScheduledExportReport.objects.get(id=1).state, constants.ScheduledReportState.REMOVED)

    def test_delete_no_permission(self):
        request = http.HttpRequest()
        request.user = models.User.objects.get(pk=2)

        self.assertEqual(dash.models.ScheduledExportReport.objects.get(id=1).state, constants.ScheduledReportState.ACTIVE)

        with self.assertRaises(exc.ForbiddenError):
            response = export_plus.ScheduledReports().delete(request, 1)

        self.assertEqual(dash.models.ScheduledExportReport.objects.get(id=1).state, constants.ScheduledReportState.ACTIVE)

    def test_delete_user_not_creator(self):
        request = http.HttpRequest()
        request.user = models.User.objects.get(pk=2)
        permission = Permission.objects.get(codename='exports_plus')
        request.user.user_permissions.add(permission)

        self.assertEqual(dash.models.ScheduledExportReport.objects.get(id=1).state, constants.ScheduledReportState.ACTIVE)

        with self.assertRaises(exc.ForbiddenError):
            response = export_plus.ScheduledReports().delete(request, 1)

        self.assertEqual(dash.models.ScheduledExportReport.objects.get(id=1).state, constants.ScheduledReportState.ACTIVE)
