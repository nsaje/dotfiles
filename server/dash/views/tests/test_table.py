#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import unittest
from mock import patch
from django.contrib.auth import models as authmodels

from django.http.request import HttpRequest
from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse
from django.conf import settings

from utils.test_helper import QuerySetMatcher, ListMatcher
from zemauth.models import User
from dash import models
from dash import constants
from dash import table
from dash import conversions_helper
from actionlog.models import ActionLog
import actionlog.constants

import reports.redshift as redshift


def copy(d):
    return {k: v for k, v in d.iteritems()}


@override_settings(
    R1_BLANK_REDIRECT_URL='http://example.com/b/{redirect_id}/z1/1/{content_ad_id}/'
)
@patch('dash.table.reports.api_touchpointconversions.query')
@patch('dash.table.reports.api_contentads.query')
class AdGroupAdsPlusTableTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

        self.maxDiff = None
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
            'cost': 100,
            'media_cost': 100,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': 100,
            'total_cost': 110,
            'billing_cost': 110,
            'license_fee': 10,
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
            'cost': 200,
            'media_cost': 200,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': None,
            'total_cost': 200,
            'billing_cost': 200,
            'license_fee': 0,
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
            'content_ad': 1,
            'date': date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'cost': 100,
            'media_cost': 100,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': 100,
            'total_cost': 110,
            'billing_cost': 110,
            'license_fee': 10,
            'visits': 40,
            'click_discrepancy': 0.2,
            'pageviews': 123,
            'percent_new_users': 33.0,
            'bounce_rate': 12.0,
            'pv_per_visit': 0.9,
            'avg_tos': 1.0,
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'cost': 200,
            'media_cost': 200,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': None,
            'total_cost': 200,
            'billing_cost': 200,
            'license_fee': 0,
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
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
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
            'clicks': 1000,
            'conversion_goal_1': 0,
            'conversion_goal_2': None,
            'conversion_goal_3': None,
            'conversion_goal_4': None,
            'conversion_goal_5': None,
            'cost': 100,
            'media_cost': 100,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': 100,
            'total_cost': 110,
            'billing_cost': 110,
            'license_fee': 10,
            'cpc': '0.0100',
            'ctr': '12.5000',
            'editable_fields': {'status_setting': {'enabled': True, 'message': None}},
            'id': '1',
            'image_urls': {
                'landscape': '/123456789.jpg?w=256&h=160&fit=crop&crop=faces&fm=jpg',
                'square': '/123456789.jpg?w=160&h=160&fit=crop&crop=faces&fm=jpg'
            },
            'impressions': 1000000,
            'status_setting': 1,
            'submission_status': [{
                'name': 'AdsNative',
                'status': 1,
                'source_state': '',
                'text': 'Pending / Paused'
            }, {
                'name': 'Gravity',
                'status': 2,
                'source_state': '(paused)',
                'text': 'Approved / Paused'
            }, {
                'name': 'Sharethrough',
                'status': 1,
                'source_state': '',
                'text': 'Pending / Paused',
            }],
            'title': u'Test Article unicode Čžš',
            'upload_time': '2015-02-22T19:00:00',
            'url': 'http://testurl.com',
            'redirector_url': 'http://example.com/b/abc/z1/1/1/',
            'visits': 40,
            'click_discrepancy': 0.2,
            'pageviews': 123,
            'percent_new_users': 33.0,
            'bounce_rate': 12.0,
            'pv_per_visit': 0.9,
            'avg_tos': 1.0,
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
            'image_urls': {
                'square': '/123456789.jpg?w=160&h=160&fit=crop&crop=faces&fm=jpg',
                'landscape': '/123456789.jpg?w=256&h=160&fit=crop&crop=faces&fm=jpg'},
            'editable_fields': {'status_setting': {'enabled': True, 'message': None}},
            'submission_status': [],
            'cost': None,
            'data_cost': None,
            'media_cost': None,
            'e_data_cost': None,
            'e_media_cost': None,
            'total_cost': None,
            'billing_cost': None,
            'license_fee': None,
            'batch_name': 'batch 1',
            'batch_id': 1,
            'display_url': 'example.com',
            'brand_name': 'Example',
            'description': 'Example description',
            'call_to_action': 'Call to action',
            'impressions': None,
            'id': '2',
            'visits': None,
            'click_discrepancy': None,
            'pageviews': None,
            'percent_new_users': None,
            'bounce_rate': None,
            'pv_per_visit': None,
            'avg_tos': None,
        }
        self.assertItemsEqual(sorted(result['data']['rows']), [expected_row_1, expected_row_2])

        self.assertIn('totals', result['data'])

        self.assertEqual(result['data']['totals'], {
            'clicks': 1500,
            'conversion_goal_1': 0,
            'conversion_goal_2': None,
            'conversion_goal_3': None,
            'conversion_goal_4': None,
            'conversion_goal_5': None,
            'cost': 200,
            'media_cost': 200,
            'data_cost': None,
            'e_data_cost': None,
            'e_media_cost': None,
            'total_cost': 200,
            'billing_cost': 200,
            'license_fee': 0,
            'cpc': '0.0200',
            'ctr': '15.5000',
            'impressions': 2000000,
            'visits': 30,
            'click_discrepancy': 0.1,
            'pageviews': 122,
            'percent_new_users': 32.0,
            'bounce_rate': 11.0,
            'pv_per_visit': 0.8,
            'avg_tos': 0.9,
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
            'cost': 100,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'cost': 200,
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
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
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
            'cost': 100,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'cost': 200,
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
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
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
            'cost': 100,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'cost': 200,
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
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        result = json.loads(response.content)

        self.assertIn('batches', result['data'])
        self.assertItemsEqual(result['data']['batches'], [{
            'id': 1,
            'name': 'batch 1'
        }])

    def test_get_batches_without_permission(self, mock_query, mock_touchpointconversions_query):

        # login without superuser permissions
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password='secret')

        ad_group = models.AdGroup.objects.get(pk=1)
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'date': date.isoformat(),
            'cpc': '0.0100',
            'clicks': 1000,
            'impressions': 1000000,
            'cost': 100,
            'ctr': '12.5000',
            'content_ad': 1
        }]
        mock_stats2 = {
            'date': date.isoformat(),
            'cpc': '0.0200',
            'clicks': 1500,
            'impressions': 2000000,
            'cost': 200,
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
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )

        result = json.loads(response.content)

        self.assertIn('batches', result['data'])
        self.assertItemsEqual(result['data']['batches'], [])

        self.assertIn('pagination', result['data'])
        self.assertEqual(result['data']['pagination'], {
            'count': 3,
            'currentPage': 1,
            'endIndex': 2,
            'numPages': 2,
            'size': 2,
            'startIndex': 1
        })

        self.assertIn('rows', result['data'])

    def test_goal_performance(self, mock_query, mock_touchpointconversins_query):
        ad_group = models.AdGroup.objects.get(pk=1)

        stats = [copy(self.mock_stats1), copy(self.mock_stats2)]

        table.set_rows_goals_performance(self.user,
                                         stats,
                                         self.mock_date,
                                         self.mock_date,
                                         [ad_group.campaign])

        self.assertEqual(stats[0]['performance'], {
            'list': [],
            'overall': None,
        })
        self.assertEqual(stats[1]['performance'], {
            'list': [],
            'overall': None,
        })

        stats = [copy(self.mock_stats1), copy(self.mock_stats2)]
        goal = models.CampaignGoal.objects.create(
            campaign=ad_group.campaign,
            type=constants.CampaignGoalKPI.CPC,
            created_dt=self.mock_date,
        )
        models.CampaignGoalValue.objects.create(
            campaign_goal=goal,
            value=0.015,
            created_dt=self.mock_date,
        )
        table.set_rows_goals_performance(self.user,
                                         stats,
                                         self.mock_date,
                                         self.mock_date,
                                         [ad_group.campaign])

        self.assertEqual(stats[0]['performance']['overall'], constants.Emoticon.HAPPY)
        self.assertEqual(stats[1]['performance']['overall'], constants.Emoticon.SAD)

    def test_primary_goal_styles(self, mock_query, mock_touchpointconversions_query):
        ad_group = models.AdGroup.objects.get(pk=1)
        stats = [copy(self.mock_stats1), copy(self.mock_stats2)]
        goal = models.CampaignGoal.objects.create(
            campaign=ad_group.campaign,
            type=constants.CampaignGoalKPI.CPC,
            created_dt=self.mock_date,
        )
        models.CampaignGoalValue.objects.create(
            campaign_goal=goal,
            value=0.015,
            created_dt=self.mock_date,
        )
        table.set_rows_goals_performance(self.user,
                                         stats,
                                         self.mock_date,
                                         self.mock_date,
                                         [ad_group.campaign])

        self.assertEqual(stats[0]['performance']['overall'], constants.Emoticon.HAPPY)
        self.assertEqual(stats[1]['performance']['overall'], constants.Emoticon.SAD)
        self.assertEqual(stats[0]['performance']['list'], [
            {'emoticon': constants.Emoticon.HAPPY, 'text': '$0.01 CPC (planned $0.02)'}
        ])
        self.assertEqual(stats[1]['performance']['list'], [
            {'emoticon': constants.Emoticon.SAD, 'text': '$0.02 CPC (planned $0.02)'}
        ])
        self.assertEqual(stats[0]['styles'], {})
        self.assertEqual(stats[1]['styles'], {})

        goal.primary = True
        goal.save()
        stats = [copy(self.mock_stats1), copy(self.mock_stats2)]
        table.set_rows_goals_performance(self.user,
                                         stats,
                                         self.mock_date,
                                         self.mock_date,
                                         [ad_group.campaign])

        self.assertEqual(stats[0]['performance']['overall'], constants.Emoticon.HAPPY)
        self.assertEqual(stats[1]['performance']['overall'], constants.Emoticon.SAD)
        self.assertEqual(stats[0]['performance']['list'], [
            {'emoticon': constants.Emoticon.HAPPY, 'text': '$0.01 CPC (planned $0.02)'},
        ])
        self.assertEqual(stats[1]['performance']['list'], [
            {'emoticon': constants.Emoticon.SAD, 'text': '$0.02 CPC (planned $0.02)'},
        ])
        self.assertEqual(stats[0]['styles'], {'cpc': constants.Emoticon.HAPPY})
        self.assertEqual(stats[1]['styles'], {'cpc': constants.Emoticon.SAD})

    def test_primary_goals_permissions(self, mock_query, mock_tpc_query):
        ad_group = models.AdGroup.objects.get(pk=1)
        mock_query.side_effect = [[copy(self.mock_stats1)], copy(self.mock_stats2)]

        user = User.objects.create_user('some@email.si', 'secret2')
        ad_group.campaign.users.add(user)
        self.client.login(username=user.email, password='secret2')
        user.user_permissions.add(
            authmodels.Permission.objects.get(codename="new_content_ads_tab")
        )

        params = {
            'page': 1,
            'order': '-cost',
            'size': 2,
            'start_date': self.mock_date.isoformat(),
            'end_date': self.mock_date.isoformat(),
        }
        response = self.client.get(
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
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
            reverse('ad_group_ads_plus_table', kwargs={'ad_group_id': ad_group.id}),
            params,
            follow=True
        )
        data = json.loads(response.content)
        self.assertEqual(data['data']['rows'][0]['performance'], {
            'list': [],
            'overall': None,
        })


class AdGroupAdsPlusTableUpdatesTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

        self.maxDiff = None
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 7, 5, 13, 22, 20)

    def test_get(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        content_ad_source = models.ContentAdSource.objects.get(pk=1)

        ActionLog(
            state=actionlog.constants.ActionState.WAITING,
            content_ad_source=content_ad_source,
            ad_group_source=ad_group_source,
            action=actionlog.constants.Action.UPDATE_CONTENT_AD,
            action_type=actionlog.constants.ActionType.AUTOMATIC
        ).save()

        params = {}
        response = self.client.get(
            reverse('ad_group_ads_plus_table_updates', kwargs={'ad_group_id': ad_group.id}),
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
        self.assertEqual(result['data']['notifications'], {
            '1': {
                'message': 'Status is being changed from Paused to Enabled',
                'in_progress': True
            }
        })

        self.assertIn('in_progress', result['data'])
        self.assertEqual(result['data']['in_progress'], True)

        self.assertIn('rows', result['data'])
        expected_submission_status = [{
            'status': 1,
            'source_state': '',
            'text': 'Pending / Paused',
            'name': 'AdsNative'
        }, {
            'status': 2,
            'source_state': '(paused)',
            'text': 'Approved / Paused',
            'name': 'Gravity'
        }, {
            'status': 1,
            'source_state': '',
            'text': 'Pending / Paused',
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

    def test_get_supply_dash_url_pending(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD]
        ad_group_source.source_campaign_key = settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE

        result = ad_group_source.get_supply_dash_url()

        self.assertIsNone(result)

    def test_get_supply_dash_disabled_message(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD
        ]

        view = table.SourcesTable()
        result = view._get_supply_dash_disabled_message(ad_group_source)

        self.assertIsNone(result)

    def test_get_supply_dash_disabled_message_no_dash(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = []

        view = table.SourcesTable()
        result = view._get_supply_dash_disabled_message(ad_group_source)

        self.assertEqual(result,
                         "This media source doesn't have a dashboard of its own. "
                         "All campaign management is done through Zemanta One dashboard.")

    def test_get_supply_dash_disabled_message_pending(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD
        ]
        ad_group_source.source_campaign_key = settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE

        view = table.SourcesTable()
        result = view._get_supply_dash_disabled_message(ad_group_source)

        self.assertEqual(result,
                         "Dashboard of this media source is not yet available because the "
                         "media source is still being set up for this ad group.")


@override_settings(
    R1_BLANK_REDIRECT_URL='http://example.com/b/{redirect_id}/z1/1/{content_ad_id}/'
)
@patch('dash.table.reports.api_touchpointconversions.query')
@patch('dash.table.reports.api_publishers.query')
class AdGroupPublishersTableTest(TestCase):
    fixtures = ['test_api.yaml', 'test_views.yaml']

    def setUp(self):
        password = 'secret'
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password=password)

        self.maxDiff = None
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_get(self, mock_query, mock_touchpointconversins_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'clicks': 123,
            'cost': 2.4,
            'data_cost': 0,
            'media_cost': 2.4,
            'e_data_cost': 0,
            'e_media_cost': 2.4,
            'license_fee': 0.1,
            'external_id': '12345',
            'billing_cost': 2.5,
            'total_cost': 2.5,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'domain': 'example.com',
            'exchange': 'adiant',
            'conversions': {},
        }]
        mock_stats2 = [{
            'clicks': 323,
            'cost': 2.1,
            'data_cost': 1.9,
            'media_cost': 2.1,
            'e_data_cost': 1.9,
            'e_media_cost': 2.1,
            'license_fee': 0.2,
            'external_id': '12345',
            'billing_cost': 4.2,
            'total_cost': 4.2,
            'cpc': 1.2,
            'ctr': 99.0,
            'impressions': 1560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'conversions': {},
        }]
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)
        touchpoint_conversion_goal = ad_group.campaign.conversiongoal_set.filter(
            type=conversions_helper.PIXEL_GOAL_TYPE)[0]
        mock_stats3 = [{
            'date': date.isoformat(),
            'conversion_count': 64,
            'slug': 'test_goal',
            'source': 7,
            'publisher': 'example.com',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }]
        mock_stats4 = [{
            'conversion_count': 64,
            'slug': 'test_goal',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }]
        mock_touchpointconversins_query.side_effect = [mock_stats3, mock_stats4]

        params = {
            'page': 1,
            'order': 'domain',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
        }

        response = self.client.get(
            reverse('ad_group_publishers_table', kwargs={'id_': ad_group.id, 'level_': 'ad_groups'}),
            params,
            follow=True
        )

        sources_matcher = QuerySetMatcher(models.Source.objects.all())

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=['domain', 'exchange'],
            order_fields=[],
            constraints={'ad_group': ad_group.id},
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversins_query.assert_any_call(
            date,
            date,
            breakdown=['publisher', 'source'],
            conversion_goals=[touchpoint_conversion_goal],
            constraints={'ad_group': ad_group.id},
            constraints_list=[],
        )

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=[],
            order_fields=[],
            constraints={"ad_group": ad_group.id},
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversins_query.assert_any_call(
            date,
            date,
            breakdown=[],
            conversion_goals=[touchpoint_conversion_goal],
            constraints={'ad_group': ad_group.id},
            constraints_list=[],
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('order', result['data'])
        self.assertEqual(result['data']['order'], 'domain')

        self.assertIn('pagination', result['data'])
        self.assertEqual(result['data']['pagination'], {
            'count': 1,
            'currentPage': 1,
            'endIndex': 1,
            'numPages': 1,
            'size': 2,
            'startIndex': 1
        })

        self.assertIn('rows', result['data'])

        expected_row_1 = {
            u'clicks': 123,
            u'data_cost': 0,
            u'media_cost': 2.4,
            u'e_data_cost': 0,
            u'e_media_cost': 2.4,
            u'external_id': '12345',
            u'license_fee': 0.1,
            u'billing_cost': 2.5,
            u'total_cost': 2.5,
            u'cpc': 1.3,
            u'ctr': 100.0,
            u'blacklisted': u'Active',
            u'can_blacklist_publisher': True,
            u'exchange': 'Adiant',
            u'source_id': 7,
            u'impressions': 10560,
            u'domain': 'example.com',
            u'domain_link': 'http://example.com',
            u'visits': 15,
            u'click_discrepancy': 3,
            u'pageviews': 100,
            u'new_visits': 50,
            u'percent_new_users': 0.5,
            u'bounce_rate': 0.3,
            u'pv_per_visit': 10,
            # u'performance': {u'list': [], u'overall': None},
            # u'styles': {},
            u'avg_tos': 20,
            u'conversion_goal_1': 0,
            u'conversion_goal_2': None,
            u'conversion_goal_3': None,
            u'conversion_goal_4': None,
            u'conversion_goal_5': None,
        }

        self.assertDictEqual(sorted(result['data']['rows'])[0], expected_row_1)

        self.assertIn('totals', result['data'])
        self.assertEqual(result['data']['totals'], {
            u'clicks': 323,
            u'cpc': 1.2,
            u'ctr': 99.0,
            u'media_cost': 2.1,
            u'license_fee': 0.2,
            u'total_cost': 4.2,
            u'billing_cost': 4.2,
            u'e_data_cost': 1.9,
            u'data_cost': 1.9,
            u'e_media_cost': 2.1,
            u'impressions': 1560,
            u'visits': 15,
            u'click_discrepancy': 3,
            u'pageviews': 100,
            u'new_visits': 50,
            u'percent_new_users': 0.5,
            u'bounce_rate': 0.3,
            u'pv_per_visit': 10,
            u'avg_tos': 20,
            u'conversion_goal_1': 0,
            u'conversion_goal_2': None,
            u'conversion_goal_3': None,
            u'conversion_goal_4': None,
            u'conversion_goal_5': None,
        })

    @patch('dash.table.reports.api_publishers.query_active_publishers')
    def test_get_filtered_sources(self, mock_active, mock_query, mock_touchpointconversins_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'clicks': 123,
            'cost': 2.4,
            'media_cost': 2.4,
            'e_media_cost': 2.4,
            'external_id': '12345',
            'total_cost': 2.4,
            'billing_cost': 2.4,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'domain': 'example.com',
            'exchange': 'adiant',
            'conversions': {},
        }]
        mock_stats2 = [{
            'clicks': 123,
            'cost': 2.4,
            'media_cost': 2.4,
            'e_media_cost': 2.4,
            'external_id': '12345',
            'total_cost': 2.4,
            'billing_cost': 2.4,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'conversions': {},
        }]
        mock_active.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)
        touchpoint_conversion_goal = ad_group.campaign.conversiongoal_set.filter(
            type=conversions_helper.PIXEL_GOAL_TYPE)[0]

        mock_stats3 = [{
            'date': date.isoformat(),
            'conversion_count': 64,
            'slug': 'test_goal',
            'source': 7,
            'publisher': 'example.com',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }]
        mock_stats4 = [{
            'conversion_count': 64,
            'slug': 'test_goal',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }]
        mock_touchpointconversins_query.side_effect = [mock_stats3, mock_stats4]

        params = {
            'page': 1,
            'order': 'domain',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
            'filtered_sources': '7',
            'show_blacklisted_publishers': constants.PublisherBlacklistFilter.SHOW_ACTIVE,
        }

        response = self.client.get(
            reverse('ad_group_publishers_table', kwargs={'id_': ad_group.id, 'level_': 'ad_groups'}),
            params,
            follow=True
        )

        mock_active.assert_any_call(
            date,
            date,
            breakdown_fields=['domain', 'exchange'],
            order_fields=[],
            constraints={'ad_group': ad_group.id, 'exchange': ['adiant']},
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversins_query.assert_any_call(
            date,
            date,
            breakdown=['publisher', 'source'],
            conversion_goals=[touchpoint_conversion_goal],
            constraints={'ad_group': ad_group.id, 'source': [7]},
            constraints_list=[],
        )

        mock_active.assert_any_call(
            date,
            date,
            breakdown_fields=[],
            order_fields=[],
            constraints={"ad_group": ad_group.id, 'exchange': ['adiant']},
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversins_query.assert_any_call(
            date,
            date,
            breakdown=['publisher', 'source'],
            conversion_goals=[touchpoint_conversion_goal],
            constraints={'ad_group': ad_group.id, 'source': [7]},
            constraints_list=[],
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 1)

        self.assertDictEqual(result['data']['rows'][0], {
            u'domain': u'example.com',
            u'domain_link': u'http://example.com',
            u'blacklisted': u'Active',
            u'can_blacklist_publisher': True,
            u'ctr': 100.0,
            u'exchange': u'Adiant',
            u'cpc': 1.3,
            u'media_cost': 2.4,
            u'e_media_cost': 2.4,
            u'external_id': '12345',
            u'data_cost': 0,
            u'e_data_cost': 0,
            u'license_fee': 0,
            u'total_cost': 2.4,
            u'billing_cost': 2.4,
            u'impressions': 10560,
            u'clicks': 123,
            u'source_id': 7,
            u'visits': 15,
            u'click_discrepancy': 3,
            u'pageviews': 100,
            u'new_visits': 50,
            u'percent_new_users': 0.5,
            u'bounce_rate': 0.3,
            u'pv_per_visit': 10,
            u'avg_tos': 20,
            # u'performance': {u'list': [], u'overall': None},
            # u'styles': {},
            u'conversion_goal_1': 0,
            u'conversion_goal_2': None,
            u'conversion_goal_3': None,
            u'conversion_goal_4': None,
            u'conversion_goal_5': None,
        })

        self.assertIn('totals', result['data'])
        self.assertEqual(result['data']['totals'], {
            u'ctr': 100.0,
            u'cpc': 1.3,
            u'media_cost': 2.4,
            u'e_media_cost': 2.4,
            u'data_cost': 0,
            u'e_data_cost': 0,
            u'license_fee': 0,
            u'total_cost': 2.4,
            u'billing_cost': 2.4,
            u'impressions': 10560,
            u'clicks': 123,
            u'visits': 15,
            u'click_discrepancy': 3,
            u'pageviews': 100,
            u'new_visits': 50,
            u'percent_new_users': 0.5,
            u'bounce_rate': 0.3,
            u'pv_per_visit': 10,
            u'avg_tos': 20,
            u'conversion_goal_1': 0,
            u'conversion_goal_2': None,
            u'conversion_goal_3': None,
            u'conversion_goal_4': None,
            u'conversion_goal_5': None,
        })

    """
    # TODO: Fix this
    @patch('dash.table.reports.api_publishers.query_blacklisted_publishers')
    def test_get_filtered_blacklisted_sources(self, mock_blacklisted, mock_query):
        # blacklist must first exist in order to be deleted
        models.PublisherBlacklist.objects.create(
            name="google.com",
            ad_group=models.AdGroup.objects.get(pk=1),
            source=models.Source.objects.get(tracking_slug='b1_adiant'),
            status=constants.PublisherStatus.BLACKLISTED
        )

        models.PublisherBlacklist.objects.create(
            name="google1.com",
            campaign=models.Campaign.objects.get(pk=1),
            source=models.Source.objects.get(tracking_slug='b1_adiant'),
            status=constants.PublisherStatus.BLACKLISTED
        )

        models.PublisherBlacklist.objects.create(
            name="google2.com",
            account=models.Account.objects.get(pk=1),
            source=models.Source.objects.get(tracking_slug='b1_adiant'),
            status=constants.PublisherStatus.BLACKLISTED
        )

        models.PublisherBlacklist.objects.create(
            name="google3.com",
            everywhere=True,
            source=models.Source.objects.get(tracking_slug='b1_adiant'),
            status=constants.PublisherStatus.BLACKLISTED
        )

        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
         'clicks': 123,
         'cost': 2.4,
         'cpc': 1.3,
         'ctr': 100.0,
         'impressions': 10560,
         'date': date.isoformat(),
         'domain': 'example.com',
         'exchange': 'adsnative',
        }]
        mock_stats2 = {
         'clicks': 123,
         'cost': 2.4,
         'cpc': 1.3,
         'ctr': 100.0,
         'impressions': 10560,
         'date': date.isoformat(),
        }
        mock_blacklisted.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

        params = {
            'page': 1,
            'order': 'domain',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
            'filtered_sources': '1',
            'show_blacklisted_publishers': constants.PublisherBlacklistFilter.SHOW_BLACKLISTED,
        }

        response = self.client.get(
            reverse('ad_group_publishers_table', kwargs={'id_': ad_group.id, 'level_': 'ad_groups'}),
            params,
            follow=True
        )

        expected_blacklist = [
            {
                'domain': 'google2.com',
                'adgroup_id': 1,
                'exchange': 'adiant',
            },
            {
                'domain': 'google1.com',
                'adgroup_id': 1,
                'exchange': 'adiant',
            },
            {
                'domain': 'google.com',
                'adgroup_id': 1,
                'exchange': 'adiant',
            },
            {
                'domain': 'google3.com',
                'exchange': 'adiant',
            }
        ]

        mock_blacklisted.assert_any_call(
            date,
            date,
            blacklist=expected_blacklist,
            breakdown_fields=['domain', 'exchange'],
            order_fields=['domain'],
            constraints={'ad_group': ad_group.id,
                        'exchange': ['adsnative']}
        )

        mock_blacklisted.assert_any_call(
            date,
            date,
            blacklist=expected_blacklist,
            constraints = {"ad_group": ad_group.id,
                        'exchange': ['adsnative']}
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 1)
        self.assertDictEqual(result['data']['rows'][0], {u'domain': u'example.com', u'domain_link': u'http://example.com', u'blacklisted': u'Active',
                             u'ctr': 100.0, u'exchange': u'AdsNative', u'cpc': 1.3, u'cost': 2.4, u'impressions': 10560, u'clicks': 123, u'source_id': 1})
    """

    def test_get_outbrain_blacklisted_over_quota(self, mock_query, mock_touchpointconversins_query):
        date = datetime.date(2015, 2, 22)

        for i in xrange(10):
            models.PublisherBlacklist.objects.create(
                account=models.Account.objects.get(pk=1),
                source=models.Source.objects.get(tracking_slug=constants.SourceType.OUTBRAIN),
                name='test_{}'.format(i),
                status=constants.PublisherStatus.BLACKLISTED,
            )

        mock_stats1 = [{
            'clicks': 123,
            'cost': 2.4,
            'data_cost': 0,
            'media_cost': 2.4,
            'e_data_cost': 0,
            'e_media_cost': 2.4,
            'license_fee': 0.1,
            'external_id': '12345',
            'billing_cost': 2.5,
            'total_cost': 2.5,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'domain': 'test_1',
            'exchange': 'outbrain',
            'conversions': {},
        }]
        mock_stats2 = [{
            'clicks': 323,
            'cost': 2.1,
            'data_cost': 1.9,
            'media_cost': 2.1,
            'e_data_cost': 1.9,
            'e_media_cost': 2.1,
            'license_fee': 0.2,
            'external_id': '12345',
            'billing_cost': 4.2,
            'total_cost': 4.2,
            'cpc': 1.2,
            'ctr': 99.0,
            'impressions': 1560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'conversions': {},
        }]
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)
        touchpoint_conversion_goal = ad_group.campaign.conversiongoal_set.filter(
            type=conversions_helper.PIXEL_GOAL_TYPE)[0]

        mock_stats3 = [{
            'date': date.isoformat(),
            'conversion_count': 64,
            'slug': 'test_goal',
            'source': 3,
            'publisher': 'test_1',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }]
        mock_stats4 = [{
            'conversion_count': 64,
            'slug': 'test_goal',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }]
        mock_touchpointconversins_query.side_effect = [mock_stats3, mock_stats4]

        params = {
            'page': 1,
            'order': 'domain',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
        }

        response = self.client.get(
            reverse('ad_group_publishers_table', kwargs={'id_': ad_group.id, 'level_': 'ad_groups'}),
            params,
            follow=True
        )

        sources_matcher = QuerySetMatcher(models.Source.objects.all())

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=['domain', 'exchange'],
            order_fields=[],
            constraints={'ad_group': ad_group.id},
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversins_query.assert_any_call(
            date,
            date,
            breakdown=['publisher', 'source'],
            conversion_goals=[touchpoint_conversion_goal],
            constraints={'ad_group': ad_group.id},
            constraints_list=[],
        )

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=[],
            order_fields=[],
            constraints={"ad_group": ad_group.id},
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints_list=[],
        )

        mock_touchpointconversins_query.assert_any_call(
            date,
            date,
            breakdown=[],
            conversion_goals=[touchpoint_conversion_goal],
            constraints={'ad_group': ad_group.id},
            constraints_list=[],
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('order', result['data'])
        self.assertEqual(result['data']['order'], 'domain')

        self.assertIn('pagination', result['data'])
        self.assertEqual(result['data']['pagination'], {
            'count': 1,
            'currentPage': 1,
            'endIndex': 1,
            'numPages': 1,
            'size': 2,
            'startIndex': 1
        })

        self.assertIn('rows', result['data'])

        expected_row_1 = {
            u'clicks': 123,
            u'data_cost': 0,
            u'media_cost': 2.4,
            u'e_data_cost': 0,
            u'e_media_cost': 2.4,
            u'external_id': '12345',
            u'license_fee': 0.1,
            u'billing_cost': 2.5,
            u'total_cost': 2.5,
            u'cpc': 1.3,
            u'ctr': 100.0,
            u'blacklisted': u'Blacklisted',
            u'can_blacklist_publisher': False,
            u'blacklisted_level': 'account',
            u'blacklisted_level_description': 'Blacklisted in this account',
            u'exchange': u'Outbrain',
            u'source_id': 3,
            u'impressions': 10560,
            u'domain': 'test_1',
            u'domain_link': '',
            u'visits': 15,
            u'click_discrepancy': 3,
            u'pageviews': 100,
            u'new_visits': 50,
            u'percent_new_users': 0.5,
            u'bounce_rate': 0.3,
            u'pv_per_visit': 10,
            u'avg_tos': 20,
            u'conversion_goal_1': 0,
            # u'performance': {u'list': [], u'overall': None},
            # u'styles': {},
            u'conversion_goal_2': None,
            u'conversion_goal_3': None,
            u'conversion_goal_4': None,
            u'conversion_goal_5': None,
        }

        self.assertDictEqual(sorted(result['data']['rows'])[0], expected_row_1)

        self.assertIn('totals', result['data'])
        self.assertEqual(result['data']['totals'], {
            u'clicks': 323,
            u'cpc': 1.2,
            u'ctr': 99.0,
            u'media_cost': 2.1,
            u'license_fee': 0.2,
            u'total_cost': 4.2,
            u'billing_cost': 4.2,
            u'e_data_cost': 1.9,
            u'data_cost': 1.9,
            u'e_media_cost': 2.1,
            u'impressions': 1560,
            u'visits': 15,
            u'click_discrepancy': 3,
            u'pageviews': 100,
            u'new_visits': 50,
            u'percent_new_users': 0.5,
            u'bounce_rate': 0.3,
            u'pv_per_visit': 10,
            u'avg_tos': 20,
            u'conversion_goal_1': 0,
            u'conversion_goal_2': None,
            u'conversion_goal_3': None,
            u'conversion_goal_4': None,
            u'conversion_goal_5': None,
        })

    def test_get_reverse_order(self, mock_query, mock_touchpointconversins_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'clicks': 123,
            'cost': 2.4,
            'data_cost': 0,
            'e_data_cost': 0,
            'external_id': '12345',
            'total_cost': 3,
            'billing_cost': 3,
            'media_cost': 2.4,
            'e_media_cost': 2.4,
            'license_fee': 0.6,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'domain': 'example.com',
            'exchange': 'adiant',
            'conversions': {},
        }]
        mock_stats2 = [{
            'clicks': 123,
            'cost': 2.4,
            'data_cost': 0,
            'e_data_cost': 0,
            'external_id': '12345',
            'total_cost': 3,
            'billing_cost': 3,
            'media_cost': 2.4,
            'e_media_cost': 2.4,
            'license_fee': 0.6,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'conversions': {},
        }]
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)
        touchpoint_conversion_goal = ad_group.campaign.conversiongoal_set.filter(
            type=conversions_helper.PIXEL_GOAL_TYPE)[0]

        mock_stats3 = [{
            'date': date.isoformat(),
            'conversion_count': 64,
            'slug': 'test_goal',
            'source': 7,
            'publisher': 'example.com',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }]
        mock_stats4 = [{
            'conversion_count': 64,
            'slug': 'test_goal',
            'account': 1,
            'conversion_window': touchpoint_conversion_goal.conversion_window,
        }]
        mock_touchpointconversins_query.side_effect = [mock_stats3, mock_stats4]

        params = {
            'page': 1,
            'order': '-cost',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
        }

        response = self.client.get(
            reverse('ad_group_publishers_table', kwargs={'id_': ad_group.id, 'level_': 'ad_groups'}),
            params,
            follow=True
        )

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=['domain', 'exchange'],
            order_fields=[],
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints={'ad_group': ad_group.id, },
            constraints_list=[],
        )

        mock_touchpointconversins_query.assert_any_call(
            date,
            date,
            breakdown=['publisher', 'source'],
            conversion_goals=[touchpoint_conversion_goal],
            constraints={'ad_group': ad_group.id},
            constraints_list=[],
        )

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=[],
            order_fields=[],
            conversion_goals=ListMatcher(['omniture__5', 'omniture__4', 'ga__3', 'ga__2']),
            constraints={"ad_group": ad_group.id, },
            constraints_list=[],
        )

        mock_touchpointconversins_query.assert_any_call(
            date,
            date,
            breakdown=[],
            conversion_goals=[touchpoint_conversion_goal],
            constraints={'ad_group': ad_group.id},
            constraints_list=[],
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 1)

        self.assertDictEqual(result['data']['rows'][0], {
            u'domain': u'example.com',
            u'domain_link': u'http://example.com',
            u'blacklisted': u'Active',
            u'can_blacklist_publisher': True,
            u'ctr': 100.0,
            u'exchange': u'Adiant',
            u'cpc': 1.3,
            u'media_cost': 2.4,
            u'e_media_cost': 2.4,
            u'external_id': '12345',
            u'data_cost': 0,
            u'e_data_cost': 0,
            u'total_cost': 3,
            u'billing_cost': 3,
            u'license_fee': 0.6,
            u'impressions': 10560,
            u'clicks': 123,
            u'source_id': 7,
            u'visits': 15,
            u'click_discrepancy': 3,
            u'pageviews': 100,
            u'new_visits': 50,
            u'percent_new_users': 0.5,
            u'bounce_rate': 0.3,
            u'pv_per_visit': 10,
            u'avg_tos': 20,
            # u'performance': {u'list': [], u'overall': None},
            # u'styles': {},
            u'conversion_goal_1': 0,
            u'conversion_goal_2': None,
            u'conversion_goal_3': None,
            u'conversion_goal_4': None,
            u'conversion_goal_5': None,
        })

    def test_actual_hidden(self, mock_query, mock_touchpointconversins_query):
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password='secret')

        self.user.user_permissions.add(
            authmodels.Permission.objects.get(codename="can_view_effective_costs")
        )
        self.user.user_permissions.add(
            authmodels.Permission.objects.get(codename="can_see_publishers")
        )

        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
            'clicks': 123,
            'cost': 2.4,
            'data_cost': 0,
            'e_data_cost': 0,
            'external_id': '12345',
            'total_cost': 3,
            'billing_cost': 3,
            'media_cost': 2.4,
            'e_media_cost': 2.4,
            'license_fee': 0.6,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'domain': 'example.com',
            'exchange': 'adiant',
            'conversions': {},
        }]
        mock_stats2 = [{
            'clicks': 123,
            'cost': 2.4,
            'data_cost': 0,
            'e_data_cost': 0,
            'external_id': '12345',
            'total_cost': 3,
            'billing_cost': 3,
            'media_cost': 2.4,
            'e_media_cost': 2.4,
            'license_fee': 0.6,
            'cpc': 1.3,
            'ctr': 100.0,
            'impressions': 10560,
            'date': date.isoformat(),
            'visits': 15,
            'click_discrepancy': 3,
            'pageviews': 100,
            'new_visits': 50,
            'percent_new_users': 0.5,
            'bounce_rate': 0.3,
            'pv_per_visit': 10,
            'avg_tos': 20,
            'conversions': {},
        }]
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

        params = {
            'page': 1,
            'order': '-cost',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
        }

        response = self.client.get(
            reverse('ad_group_publishers_table', kwargs={'id_': ad_group.id, 'level_': 'ad_groups'}),
            params,
            follow=True
        )

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=['domain', 'exchange'],
            order_fields=[],
            constraints={'ad_group': ad_group.id, },
            conversion_goals=[],
            constraints_list=[],
        )

        mock_query.assert_any_call(
            date,
            date,
            breakdown_fields=[],
            order_fields=[],
            constraints={"ad_group": ad_group.id, },
            conversion_goals=[],
            constraints_list=[],
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 1)

        self.assertDictEqual(result['data']['rows'][0], {
            u'domain': u'example.com',
            u'domain_link': u'http://example.com',
            u'blacklisted': u'Active',
            u'can_blacklist_publisher': True,
            u'ctr': 100.0,
            u'exchange': u'Adiant',
            u'cpc': 1.3,
            u'e_media_cost': 2.4,
            u'external_id': '12345',
            u'e_data_cost': 0,
            u'billing_cost': 3,
            u'license_fee': 0.6,
            u'impressions': 10560,
            u'clicks': 123,
            u'source_id': 7,
        })


@patch('reports.redshift.get_cursor')
class AllAccountsSourcesTableTest(TestCase):
    fixtures = ['test_aggregation.yaml']

    def setUp(self):
        self.normal_user = User.objects.get(pk=1)
        self.redshift_user = User.objects.get(pk=2)

        redshift_perm = authmodels.Permission.objects.get(codename="can_see_redshift_postclick_statistics")
        self.redshift_user.user_permissions.add(redshift_perm)

        redshift.STATS_DB_NAME = 'default'

    def test_get_normal_all_accounts_table(self, mock_get_cursor):
        t = table.AllAccountsSourcesTable(self.normal_user, 1, [])
        today = datetime.datetime.utcnow()
        r = HttpRequest()
        t.get_stats(r, today, today)
        self.assertFalse(mock_get_cursor().dictfetchall.called)

    def test_get_redshift_all_accounts_table(self, mock_get_cursor):
        t = table.AllAccountsSourcesTable(self.redshift_user, 1, [])
        today = datetime.datetime.utcnow()
        r = HttpRequest()
        t.get_stats(r, today, today)
        self.assertTrue(mock_get_cursor().dictfetchall.called)

    def test_funcs(self, mock_get_cursor):
        t = table.AllAccountsSourcesTable(self.redshift_user, 1, [])
        today = datetime.datetime.utcnow()
        self.assertTrue(t.has_complete_postclick_metrics(today, today))

        self.assertFalse(t.is_sync_in_progress())
