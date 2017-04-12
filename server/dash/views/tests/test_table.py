# -*- coding: utf-8 -*-
import datetime
import json
from mock import patch
from django.contrib.auth import models as authmodels

from django.http.request import HttpRequest
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.conf import settings

from utils.test_helper import QuerySetMatcher, ListMatcher
from zemauth.models import User
from dash import models
from dash import constants
from dash import table
from dash import conversions_helper
from utils import test_helper
from dash.views import helpers

import reports.redshift as redshift


def copy(d):
    return {k: v for k, v in d.iteritems()}


@override_settings(
    R1_BLANK_REDIRECT_URL='http://example.com/b/{redirect_id}/z1/1/{content_ad_id}/'
)
@patch('dash.table.reports.api_touchpointconversions.query')
@patch('dash.table.reports.api_contentads.query')
class AdGroupAdsTableTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

        self.patcher = patch('reports.api_contentads.has_complete_postclick_metrics')
        mock_has_complete_postclick_metrics = self.patcher.start()
        mock_has_complete_postclick_metrics.return_value = True

        self.mock_date = datetime.date(2015, 2, 22)
        self.mock_stats1 = {
            'ctr': '12.5000',
            'content_ad': 1,
            'date': self.mock_date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'media_cost': 100,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': 100,
            'billing_cost': 110,
            'license_fee': 10,
            'margin': 11,
            'agency_total': 121,
            'visits': 40,
            'click_discrepancy': 0.2,
            'pageviews': 123,
            'percent_new_users': 33.0,
            'bounce_rate': 12.0,
            'pv_per_visit': 0.9,
            'avg_tos': 1.0,
        }
        self.mock_stats2 = {
            'date': self.mock_date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'media_cost': 200,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': 200,
            'billing_cost': 200,
            'license_fee': 0,
            'margin': 20,
            'agency_total': 220,
            'ctr': '15.5000',
            'content_ad': 2,
            'visits': 30,
            'click_discrepancy': 0.1,
            'pageviews': 122,
            'percent_new_users': 32.0,
            'bounce_rate': 11.0,
            'pv_per_visit': 0.8,
            'avg_tos': 0.9,
        }

    def tearDown(self):
        self.patcher.stop()

    def test_get(self, mock_query, mock_touchpointconversins_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'ctr': '12.5000',
            'cpm': '0.1',
            'content_ad': 1,
            'date': date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'media_cost': 100,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': 100,
            'billing_cost': 110,
            'license_fee': 10,
            'margin': 11,
            'agency_total': 121,
            'visits': 40,
            'click_discrepancy': 0.2,
            'pageviews': 123,
            'percent_new_users': 33.0,
            'bounce_rate': 12.0,
            'pv_per_visit': 0.9,
            'avg_tos': 1.0,
            'returning_users': 20,
            'unique_users': 35,
            'new_users': 15,
            'bounced_visits': 6,
            'avg_cost_per_visit': 0.15,
            'avg_cost_per_pageview': 0.123,
            'avg_cost_per_minute': 0.753,
            'avg_cost_for_new_visitor': 0.221,
            'avg_cost_per_non_bounced_visit': 0.332,
            'non_bounced_visits': 5,
            'total_seconds': 14,
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'cpm': '0.1',
            'clicks': 1500,
            'impressions': 2000000,
            'media_cost': 200,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': None,
            'billing_cost': 200,
            'license_fee': 0,
            'margin': 20,
            'agency_total': 220,
            'ctr': '15.5000',
            'content_ad': 2,
            'visits': 30,
            'returning_users': 20,
            'unique_users': 30,
            'new_users': 10,
            'click_discrepancy': 0.1,
            'pageviews': 122,
            'percent_new_users': 32.0,
            'bounce_rate': 11.0,
            'pv_per_visit': 0.8,
            'avg_tos': 0.9,
            'bounced_visits': 6,
            'avg_cost_per_visit': 0.15,
            'avg_cost_per_pageview': 0.123,
            'avg_cost_per_minute': 0.753,
            'avg_cost_for_new_visitor': 0.221,
            'avg_cost_per_non_bounced_visit': 0.332,
            'non_bounced_visits': 5,
            'total_seconds': 14,
        }
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

        params = {
            'page': 1,
            'order': 'title',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
        }

        response = self.client.get(
            reverse('ad_group_ads_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        sources_matcher = QuerySetMatcher(models.Source.objects.all())

        mock_query.assert_any_call(
            date,
            date,
            breakdown=['content_ad'],
            order=[],
            ignore_diff_rows=True,
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(
                type=constants.ConversionGoalType.PIXEL)],
            ad_group=ad_group,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            ad_group=ad_group,
            breakdown=[],
            order=[],
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(
                type=constants.ConversionGoalType.PIXEL)],
            ignore_diff_rows=True,
            source=sources_matcher
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('last_change', result['data'])
        self.assertEqual(result['data']['last_change'], '2015-02-22T19:00:00')

        self.assertIn('order', result['data'])
        self.assertEqual(result['data']['order'], 'title')

        self.assertIn('pagination', result['data'])
        self.assertEqual(result['data']['pagination'], {
            'count': 2,
            'currentPage': 1,
            'endIndex': 2,
            'numPages': 1,
            'size': 2,
            'startIndex': 1
        })

        self.assertIn('rows', result['data'])

        for row in result['data']['rows']:
            row['submission_status'] = sorted(row['submission_status'])

        expected_row_1 = {
            'batch_name': 'batch 1',
            'archived': False,
            'batch_id': 1,
            'display_url': 'example.com',
            'brand_name': 'Example',
            'description': 'Example description',
            'call_to_action': 'Call to action',
            'label': '',
            'clicks': 1000,
            'pixel_1_24': 0,
            'pixel_1_168': 0,
            'pixel_1_720': 0,
            'pixel_1_2160': 0,
            'conversion_goal_2': None,
            'conversion_goal_3': None,
            'conversion_goal_4': None,
            'conversion_goal_5': None,
            'media_cost': 100,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': 100,
            'billing_cost': 110,
            'license_fee': 10,
            'margin': 11,
            'agency_total': 121,
            'cpc': '0.0100',
            'cpm': '0.1',
            'ctr': '12.5000',
            'editable_fields': {'status_setting': {'enabled': True, 'message': None}},
            'id': '1',
            'image_urls': {
                'landscape': '/123456789.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg',
                'square': '/123456789.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg'
            },
            'image_hash': '987654321',
            'impressions': 1000000,
            'status_setting': 1,
            'submission_status': [{
                'name': 'AdsNative',
                'status': 1,
                'source_state': '(paused)',
                'text': 'Pending'
            }, {
                'name': 'Gravity',
                'status': 2,
                'source_state': '(paused)',
                'text': 'Approved'
            }, {
                'name': 'Sharethrough',
                'status': 1,
                'source_state': '',
                'text': 'Pending',
            }],
            'title': u'Test Article unicode Čžš',
            'upload_time': '2015-02-22T19:00:00',
            'url': 'http://testurl.com',
            'redirector_url': 'http://example.com/b/abc/z1/1/1/',
            'visits': 40,
            'returning_users': 20,
            'bounced_visits': 6,
            'unique_users': 35,
            'new_users': 15,
            'click_discrepancy': 0.2,
            'pageviews': 123,
            'percent_new_users': 33.0,
            'bounce_rate': 12.0,
            'pv_per_visit': 0.9,
            'avg_tos': 1.0,
            'avg_cost_per_visit': 0.15,
            'avg_cost_per_pageview': 0.123,
            'avg_cost_per_minute': 0.753,
            'avg_cost_for_new_visitor': 0.221,
            'avg_cost_per_non_bounced_visit': 0.332,
            'avg_cost_per_pixel_1_24': None,
            'avg_cost_per_pixel_1_168': None,
            'avg_cost_per_pixel_1_720': None,
            'avg_cost_per_pixel_1_2160': None,
            'non_bounced_visits': 5,
            'total_seconds': 14,
            'performance': {
                'list': [],
                'overall': None,
            },
            'styles': {},
        }

        expected_row_2 = {
            'archived': False,
            'status_setting': 2,
            'upload_time': '2015-02-22T19:00:00',
            'ctr': None,
            'title': 'Test Article with no content_ad_sources 1',
            'url': 'http://testurl.com',
            'redirector_url': 'http://example.com/b/abc/z1/1/2/',
            'clicks': None,
            'cpc': None,
            'cpm': None,
            'image_urls': {
                'square': '/123456789.jpg?w=160&h=160&fit=crop&crop=center&fm=jpg',
                'landscape': '/123456789.jpg?w=256&h=160&fit=crop&crop=center&fm=jpg'},
            'image_hash': '987654321',
            'editable_fields': {'status_setting': {'enabled': True, 'message': None}},
            'submission_status': [],
            'data_cost': None,
            'media_cost': None,
            'e_data_cost': None,
            'e_media_cost': None,
            'billing_cost': None,
            'license_fee': None,
            'margin': None,
            'agency_total': None,
            'batch_name': 'batch 1',
            'batch_id': 1,
            'display_url': 'example.com',
            'brand_name': 'Example',
            'description': 'Example description',
            'call_to_action': 'Call to action',
            'label': '',
            'impressions': None,
            'id': '2',
            'visits': None,
            'click_discrepancy': None,
            'pageviews': None,
            'percent_new_users': None,
            'bounce_rate': None,
            'pv_per_visit': None,
            'avg_tos': None,
            'avg_cost_per_visit': None,
            'avg_cost_per_pageview': None,
            'avg_cost_per_minute': None,
            'avg_cost_for_new_visitor': None,
            'avg_cost_per_non_bounced_visit': None,
            'non_bounced_visits': None,
            'total_seconds': None,
            'returning_users': None,
            'unique_users': None,
            'new_users': None,
            'bounced_visits': None,
        }
        self.assertItemsEqual(sorted(result['data']['rows']), [expected_row_1, expected_row_2])

        self.assertIn('totals', result['data'])

        self.assertDictEqual(result['data']['totals'], {
            'clicks': 1500,
            'pixel_1_24': 0,
            'pixel_1_168': 0,
            'pixel_1_720': 0,
            'pixel_1_2160': 0,
            'conversion_goal_2': None,
            'conversion_goal_3': None,
            'conversion_goal_4': None,
            'conversion_goal_5': None,
            'media_cost': 200,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': None,
            'billing_cost': 200,
            'license_fee': 0,
            'margin': 20,
            'agency_total': 220,
            'cpc': '0.0200',
            'cpm': '0.1',
            'ctr': '15.5000',
            'impressions': 2000000,
            'visits': 30,
            'returning_users': 20,
            'bounced_visits': 6,
            'unique_users': 30,
            'new_users': 10,
            'click_discrepancy': 0.1,
            'pageviews': 122,
            'percent_new_users': 32.0,
            'bounce_rate': 11.0,
            'pv_per_visit': 0.8,
            'avg_tos': 0.9,
            'avg_cost_per_visit': 0.15,
            'avg_cost_per_pageview': 0.123,
            'avg_cost_per_minute': 0.753,
            'avg_cost_for_new_visitor': 0.221,
            'avg_cost_per_non_bounced_visit': 0.332,
            'avg_cost_per_pixel_1_24': None,
            'avg_cost_per_pixel_1_168': None,
            'avg_cost_per_pixel_1_720': None,
            'avg_cost_per_pixel_1_2160': None,
            'non_bounced_visits': 5,
            'total_seconds': 14,
        })

        batches = models.UploadBatch.objects.filter(
            id__in=(1, 2),
            status=constants.UploadBatchStatus.DONE
        )
        self.assertItemsEqual(batches, [])
        self.assertIn('batches', result['data'])
        self.assertEqual(result['data']['batches'], [])

    def test_get_filtered_sources(self, mock_query, mock_touchpointconversions_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'date': date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'ctr': '15.5000',
            'content_ad': 1
        }
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

        params = {
            'page': 1,
            'order': 'title',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
            'filtered_sources': '1,2'
        }

        response = self.client.get(
            reverse('ad_group_ads_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        sources_matcher = QuerySetMatcher(models.Source.objects.filter(id__in=[1, 2]))

        mock_query.assert_any_call(
            date,
            date,
            breakdown=['content_ad'],
            order=[],
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(
                type=constants.ConversionGoalType.PIXEL)],
            ad_group=ad_group,
            ignore_diff_rows=True,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            breakdown=[],
            order=[],
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(
                type=constants.ConversionGoalType.PIXEL)],
            ignore_diff_rows=True,
            ad_group=ad_group,
            source=sources_matcher
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 1)
        self.assertEqual(result['data']['rows'][0]['id'], '1')

    def test_get_order(self, mock_query, mock_touchpointconversions_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'date': date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'ctr': '15.5000',
            'content_ad': 1
        }
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

        params = {
            'page': 1,
            'order': '-title',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
        }

        response = self.client.get(
            reverse('ad_group_ads_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        sources_matcher = QuerySetMatcher(models.Source.objects.all())

        mock_query.assert_any_call(
            date,
            date,
            breakdown=['content_ad'],
            order=[],
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(
                type=constants.ConversionGoalType.PIXEL)],
            ignore_diff_rows=True,
            ad_group=ad_group,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            ad_group=ad_group,
            breakdown=[],
            order=[],
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(
                type=constants.ConversionGoalType.PIXEL)],
            ignore_diff_rows=True,
            source=sources_matcher
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('order', result['data'])
        self.assertEqual(result['data']['order'], '-title')

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 2)
        self.assertEqual(result['data']['rows'][0]['title'], u'Test Article with no content_ad_sources 1')
        self.assertEqual(result['data']['rows'][1]['title'], u'Test Article unicode \u010c\u017e\u0161')

    def test_get_batches(self, mock_query, mock_touchpointconversions_query):
        ad_group = models.AdGroup.objects.get(pk=1)
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'date': date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'ctr': '15.5000',
            'content_ad': 1
        }
        mock_query.side_effect = [mock_stats1, mock_stats2]

        params = {
            'page': 1,
            'order': '-title',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
        }

        uploadBatches = models.UploadBatch.objects.filter(id__in=(1, 2))
        for batch in uploadBatches:
            batch.status = constants.UploadBatchStatus.DONE
            batch.save()

        response = self.client.get(
            reverse('ad_group_ads_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        result = json.loads(response.content)

        self.assertIn('batches', result['data'])
        self.assertItemsEqual(result['data']['batches'], [{
            'id': 1,
            'name': 'batch 1'
        }])

    def test_primary_goals_permissions(self, mock_query, mock_tpc_query):
        ad_group = models.AdGroup.objects.get(pk=1)
        mock_query.side_effect = [[copy(self.mock_stats1)], copy(self.mock_stats2)]

        user = User.objects.create_user('some@email.si', 'secret2')
        ad_group.campaign.users.add(user)
        self.client.login(username=user.email, password='secret2')
        user.user_permissions.add(
            authmodels.Permission.objects.get(codename="can_view_platform_cost_breakdown")
        )

        params = {
            'page': 1,
            'order': '-e_media_cost',
            'size': 2,
            'start_date': self.mock_date.isoformat(),
            'end_date': self.mock_date.isoformat(),
        }
        response = self.client.get(
            reverse('ad_group_ads_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )
        data = json.loads(response.content)

        self.assertFalse('performance' in data['data']['rows'][0])

        mock_query.side_effect = [[copy(self.mock_stats1)], copy(self.mock_stats2)]
        user.user_permissions.add(
            authmodels.Permission.objects.get(codename="campaign_goal_performance")
        )

        response = self.client.get(
            reverse('ad_group_ads_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )
        data = json.loads(response.content)
        self.assertEqual(data['data']['rows'][0]['performance'], {
            'list': [],
            'overall': None,
        })


class AdGroupAdsTableUpdatesTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 7, 5, 13, 22, 20)

    def test_get(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        params = {}
        response = self.client.get(
            reverse('ad_group_ads_table_updates', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('last_change', result['data'])
        self.assertEqual(result['data']['last_change'], '2015-02-22T19:00:00')

        self.assertIn('notifications', result['data'])
        self.assertEqual(result['data']['notifications'], {})

        self.assertIn('in_progress', result['data'])
        self.assertEqual(result['data']['in_progress'], False)

        self.assertIn('rows', result['data'])
        expected_submission_status = [{
            'status': 1,
            'source_state': '(paused)',
            'text': 'Pending',
            'name': 'AdsNative'
        }, {
            'status': 2,
            'source_state': '(paused)',
            'text': 'Approved',
            'name': 'Gravity'
        }, {
            'status': 1,
            'source_state': '',
            'text': 'Pending',
            'name': 'Sharethrough'
        }]
        self.assertItemsEqual(result['data']['rows']['1']['submission_status'], expected_submission_status)
        self.assertEqual(result['data']['rows']['1']['status_setting'], 1)


class AdGroupSourceTableSupplyDashTest(TestCase):
    fixtures = ['test_api.yaml']

    def test_get_supply_dash_url(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD]

        result = ad_group_source.get_supply_dash_url()

        self.assertEqual(result, '/supply_dash/?ad_group_id=1&source_id=1')

    def test_get_supply_dash_url_no_dash(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = []

        result = ad_group_source.get_supply_dash_url()

        self.assertIsNone(result)

    def test_get_source_supply_dash_disabled_message(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD
        ]

        result = helpers.get_source_supply_dash_disabled_message(ad_group_source, ad_group_source.source)

        self.assertIsNone(result)

    def test_get_source_supply_dash_disabled_message_no_dash(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = []

        result = helpers.get_source_supply_dash_disabled_message(ad_group_source, ad_group_source.source)

        self.assertEqual(result,
                         "This media source doesn't have a dashboard of its own. "
                         "All campaign management is done through Zemanta One dashboard.")
