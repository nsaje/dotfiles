#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
from mock import patch

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

from utils.test_helper import QuerySetMatcher
from zemauth.models import User
from dash import models
from dash import constants
from dash import views
from actionlog.models import ActionLog
import actionlog.constants


@patch('dash.views.table.reports.api_contentads.query')
class AdGroupAdsPlusTableTest(TestCase):
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
            ad_group=ad_group,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            ad_group=ad_group,
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

        self.assertItemsEqual(result['data']['rows'], [{
            'batch_name': 'batch 1',
            'archived': False,
            'batch_id': 1,
            'display_url': 'example.com',
            'brand_name': 'Example',
            'description': 'Example description',
            'call_to_action': 'Call to action',
            'clicks': 1000,
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
            }],
            'title': u'Test Article unicode Čžš',
            'upload_time': '2015-02-22T19:00:00',
            'url': 'http://testurl.com',
        }, {
            'archived': False,
            'status_setting': 2,
            'upload_time': '2015-02-22T19:00:00',
            'ctr': None,
            'title': 'Test Article with no content_ad_sources 1',
            'url': 'http://testurl.com',
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
            'id': '2'
        }])

        self.assertIn('totals', result['data'])
        self.assertEqual(result['data']['totals'], {
            'clicks': 1500,
            'cost': 200,
            'cpc': '0.0200',
            'ctr': '15.5000',
            'impressions': 2000000
        })

        batches = models.UploadBatch.objects.filter(
            id__in=(1, 2),
            status=constants.UploadBatchStatus.DONE
        )
        self.assertItemsEqual(batches, [])
        self.assertIn('batches', result['data'])
        self.assertEqual(result['data']['batches'], [])

    def test_get_filtered_sources(self, mock_query):
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
            ad_group=ad_group,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
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

    def test_get_order(self, mock_query):
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
            ad_group=ad_group,
            source=sources_matcher
        )

        mock_query.assert_any_call(
            date,
            date,
            ad_group=ad_group,
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

    def test_get_batches(self, mock_query):
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

    def test_get_batches_without_permission(self, mock_query):

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

        view = views.table.SourcesTable()
        result = view._get_supply_dash_url(ad_group_source)

        self.assertEqual(result, '/supply_dash/?ad_group_id=1&source_id=1')

    def test_get_supply_dash_url_no_dash(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = []

        view = views.table.SourcesTable()
        result = view._get_supply_dash_url(ad_group_source)

        self.assertIsNone(result)

    def test_get_supply_dash_url_pending(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD]
        ad_group_source.source_campaign_key = settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE

        view = views.table.SourcesTable()
        result = view._get_supply_dash_url(ad_group_source)

        self.assertIsNone(result)

    def test_get_supply_dash_disabled_message(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.HAS_3RD_PARTY_DASHBOARD
        ]

        view = views.table.SourcesTable()
        result = view._get_supply_dash_disabled_message(ad_group_source)

        self.assertIsNone(result)

    def test_get_supply_dash_disabled_message_no_dash(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source.source.source_type.available_actions = []

        view = views.table.SourcesTable()
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

        view = views.table.SourcesTable()
        result = view._get_supply_dash_disabled_message(ad_group_source)

        self.assertEqual(result,
                         "Dashboard of this media source is not yet available because the "
                         "media source is still being set up for this ad group.")


class AdGroupSourceTableEditableFieldsTest(TestCase):
    fixtures = ['test_api.yaml']

    class DatetimeMock(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2015, 6, 5, 13, 22, 23)

    def test_get_editable_fields_status_setting_enabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]

        ad_group_source.ad_group.content_ads_tab_with_cms = False

        view = views.table.SourcesTable()
        result = view._get_editable_fields_status_setting(ad_group_source, ad_group_settings, ad_group_source_settings)

        self.assertEqual(result, {
            'enabled': True,
            'message': None
        })

    def test_get_editable_fields_status_setting_disabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)

        ad_group_source.source.source_type.available_actions = []

        ad_group_source.ad_group.content_ads_tab_with_cms = False

        view = views.table.SourcesTable()
        result = view._get_editable_fields_status_setting(ad_group_source, ad_group_settings, ad_group_source_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'This source must be managed manually.'
        })

    def test_get_editable_fields_status_setting_maintenance(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]
        ad_group_source.source.maintenance = True

        ad_group_source.ad_group.content_ads_tab_with_cms = False

        view = views.table.SourcesTable()
        result = view._get_editable_fields_status_setting(ad_group_source, ad_group_settings, ad_group_source_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'This source is currently in maintenance mode.'
        })

    def test_get_editable_fields_status_setting_no_cms_support(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]

        ad_group_source.ad_group.content_ads_tab_with_cms = True

        ad_group_source.can_manage_content_ads = False

        view = views.table.SourcesTable()
        result = view._get_editable_fields_status_setting(ad_group_source, ad_group_settings, ad_group_source_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'Please contact support to enable this source.'
        })

    def test_get_editable_fields_status_setting_no_dma_support(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)
        ad_group_source_settings = models.AdGroupSourceSettings.objects.get(pk=1)
        ad_group_source_settings.state = constants.AdGroupSourceSettingsState.INACTIVE

        ad_group_settings = models.AdGroupSettings.objects.get(pk=1)
        ad_group_settings.target_regions = ['693']

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_STATE]
        ad_group_source.ad_group.content_ads_tab_with_cms = False

        view = views.table.SourcesTable()

        result = view._get_editable_fields_status_setting(ad_group_source, ad_group_settings, ad_group_source_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'This source can not be enabled because it does not support DMA targeting.'
        })

    def test_get_editable_fields_bid_cpc_enabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_CPC]

        view = views.table.SourcesTable()
        result = view._get_editable_fields_bid_cpc(ad_group_source, ad_group_settings)

        self.assertEqual(result, {
            'enabled': True,
            'message': None
        })

    def test_get_editable_fields_bid_cpc_disabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None

        ad_group_source.source.source_type.available_actions = []

        view = views.table.SourcesTable()
        result = view._get_editable_fields_bid_cpc(ad_group_source, ad_group_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'This media source doesn\'t support setting this value through the dashboard.'
        })

    def test_get_editable_fields_bid_cpc_maintenance(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None

        ad_group_source.source.source_type.available_actions = [constants.SourceAction.CAN_UPDATE_CPC]
        ad_group_source.source.maintenance = True

        view = views.table.SourcesTable()
        result = view._get_editable_fields_bid_cpc(ad_group_source, ad_group_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'This value cannot be edited because the media source is currently in maintenance.'
        })

    @patch('dash.views.table.datetime.datetime', DatetimeMock)
    def test_get_editable_fields_bid_cpc_end_date_past(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = datetime.datetime(2015, 1, 1)

        ad_group_source.source.source_type.available_actions = []

        view = views.table.SourcesTable()
        result = view._get_editable_fields_bid_cpc(ad_group_source, ad_group_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.'
        })

    def test_get_editable_fields_daily_budget_enabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None

        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_AUTOMATIC
        ]

        view = views.table.SourcesTable()
        result = view._get_editable_fields_daily_budget(ad_group_source, ad_group_settings)

        self.assertEqual(result, {
            'enabled': True,
            'message': None
        })

    def test_get_editable_fields_daily_budget_disabled(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None

        ad_group_source.source.source_type.available_actions = []

        view = views.table.SourcesTable()
        result = view._get_editable_fields_daily_budget(ad_group_source, ad_group_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'This media source doesn\'t support setting this value through the dashboard.'
        })

    def test_get_editable_fields_daily_budget_maintenance(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = None

        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.CAN_UPDATE_DAILY_BUDGET_AUTOMATIC
        ]
        ad_group_source.source.maintenance = True

        view = views.table.SourcesTable()
        result = view._get_editable_fields_daily_budget(ad_group_source, ad_group_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'This value cannot be edited because the media source is currently in maintenance.'
        })

    @patch('dash.views.table.datetime.datetime', DatetimeMock)
    def test_get_editable_fields_daily_budget_end_date_past(self):
        ad_group_source = models.AdGroupSource.objects.get(pk=1)

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.end_date = datetime.datetime(2015, 1, 1)

        ad_group_source.source.source_type.available_actions = []

        view = views.table.SourcesTable()
        result = view._get_editable_fields_daily_budget(ad_group_source, ad_group_settings)

        self.assertEqual(result, {
            'enabled': False,
            'message': 'The ad group has end date set in the past. No modifications to media source parameters are possible.'
        })
