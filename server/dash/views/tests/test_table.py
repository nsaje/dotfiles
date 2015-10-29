#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
from mock import patch
from django.contrib.auth import models as authmodels

from django.http.request import HttpRequest
from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse
from django.conf import settings

from utils.test_helper import QuerySetMatcher
from zemauth.models import User
from dash import models
from dash import constants
from dash import table
from actionlog.models import ActionLog
import actionlog.constants

import reports.redshift as redshift


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
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(type=constants.ConversionGoalType.PIXEL)],
            ad_group=ad_group,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            ad_group=ad_group,
            breakdown=[],
            order=[],
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(type=constants.ConversionGoalType.PIXEL)],
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
            'conversion_goal_2': None,
            'cost': 100,
            'cpc': '0.0100',
            'ctr': '12.5000',
            'editable_fields': {'status_setting': {'enabled': True, 'message': None}},
            'id': '1',
            'image_urls': {
                'landscape': '/123456789/256x160.jpg',
                'square': '/123456789/160x160.jpg'
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
                'square': '/123456789/160x160.jpg',
                'landscape': '/123456789/256x160.jpg'},
            'editable_fields': {'status_setting': {'enabled': True, 'message': None}},
            'submission_status': [],
            'cost': None,
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
            'conversion_goal_2': None,
            'cost': 200,
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
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(type=constants.ConversionGoalType.PIXEL)],
            ad_group=ad_group,
            ignore_diff_rows=True,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            breakdown=[],
            order=[],
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(type=constants.ConversionGoalType.PIXEL)],
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
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(type=constants.ConversionGoalType.PIXEL)],
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
            conversion_goals=[cg.get_stats_key() for cg in ad_group.campaign.conversiongoal_set.exclude(type=constants.ConversionGoalType.PIXEL)],
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
        self.assertEqual(result['data']['rows'], {
            '1': {
                'submission_status': [{
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
                }],
                'status_setting': 1
            }
        })


class AdGroupSourceTableSupplyDashTest(TestCase):
    fixtures = ['test_api.yaml']

    def test_get_supply_dash_url(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD]

        view = table.SourcesTable()
        result = view._get_supply_dash_url(ad_group_source)

        self.assertEqual(result, '/supply_dash/?ad_group_id=1&source_id=1')

    def test_get_supply_dash_url_no_dash(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = []

        view = table.SourcesTable()
        result = view._get_supply_dash_url(ad_group_source)

        self.assertIsNone(result)

    def test_get_supply_dash_url_pending(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD]
        ad_group_source.source_campaign_key = settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE

        view = table.SourcesTable()
        result = view._get_supply_dash_url(ad_group_source)

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

    def test_get(self, mock_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
         'clicks': 123,
         'cost': 2.4,
         'cpc': 1.3,
         'ctr': 100.0,
         'impressions': 10560,
         'date': date.isoformat(),
         'domain': 'example.com',
         'exchange': 'someexchange',
        }]
        mock_stats2 = {
         'clicks': 323,
         'cost': 2.1,
         'cpc': 1.2,
         'ctr': 99.0,
         'impressions': 1560,
         'date': date.isoformat(),
        }
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

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
            order_fields=['domain'],
            constraints={'ad_group': ad_group.id}
        )

        mock_query.assert_any_call(
            date,
            date,
            constraints={"ad_group": ad_group.id},
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
            u'cost': 2.4,
            u'cpc': 1.3,
            u'ctr': 100.0,
            u'domain': None,
            u'domain_link': u'',
            u'blacklisted': u'Active',
            u'exchange': 'someexchange',
            u'impressions': 10560,
            u'domain': 'example.com',
            u'domain_link': 'http://example.com',
        }

        self.assertDictEqual(sorted(result['data']['rows'])[0], expected_row_1)

        self.assertIn('totals', result['data'])

        self.assertEqual(result['data']['totals'], {	u'clicks': 323,
                                                        u'cost': 2.1,
                                                        u'cpc': 1.2,
                                                        u'ctr': 99.0,
                                                        u'impressions': 1560})

    def test_get_filtered_sources(self, mock_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
         'clicks': 123,
         'cost': 2.4,
         'cpc': 1.3,
         'ctr': 100.0,
         'impressions': 10560,
         'date': date.isoformat(),
         'domain': 'example.com',
         'exchange': 'someexchange',
        }]
        mock_stats2 = {
         'clicks': 123,
         'cost': 2.4,
         'cpc': 1.3,
         'ctr': 100.0,
         'impressions': 10560,
         'date': date.isoformat(),
        }
        mock_query.side_effect = [mock_stats1, mock_stats2]

        ad_group = models.AdGroup.objects.get(pk=1)

        params = {
            'page': 1,
            'order': 'domain',
            'size': 2,
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
            'filtered_sources': '1'
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
            order_fields=['domain'],
            constraints={'ad_group': ad_group.id,
                        'exchange': ['adsnative']}
        )

        mock_query.assert_any_call(
            date,
            date,
            constraints = {"ad_group": ad_group.id,
                        'exchange': ['adsnative']}
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 1)
        self.assertDictEqual(result['data']['rows'][0], {u'domain': u'example.com', u'domain_link': u'http://example.com', u'blacklisted': u'Active', u'ctr': 100.0, u'exchange': u'someexchange', u'cpc': 1.3, u'cost': 2.4, u'impressions': 10560, u'clicks': 123})

    def test_get_reverse_order(self, mock_query):
        date = datetime.date(2015, 2, 22)

        mock_stats1 = [{
         'clicks': 123,
         'cost': 2.4,
         'cpc': 1.3,
         'ctr': 100.0,
         'impressions': 10560,
         'date': date.isoformat(),
         'domain': 'example.com',
         'exchange': 'someexchange',
        }]
        mock_stats2 = {
         'clicks': 123,
         'cost': 2.4,
         'cpc': 1.3,
         'ctr': 100.0,
         'impressions': 10560,
         'date': date.isoformat(),
        }
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
            order_fields=['-cost'],
            constraints={'ad_group': ad_group.id, }
        )

        mock_query.assert_any_call(
            date,
            date,
            constraints={"ad_group": ad_group.id, }
        )

        result = json.loads(response.content)

        self.assertIn('success', result)
        self.assertEqual(result['success'], True)

        self.assertIn('data', result)

        self.assertIn('rows', result['data'])
        self.assertEqual(len(result['data']['rows']), 1)
        self.assertDictEqual(result['data']['rows'][0], {u'domain': u'example.com', u'domain_link': u'http://example.com', u'blacklisted': u'Active', u'ctr': 100.0, u'exchange': u'someexchange', u'cpc': 1.3, u'cost': 2.4, u'impressions': 10560, u'clicks': 123})


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
