import datetime
import json

from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse
from django.http.request import HttpRequest

import dash.constants
import dash.models

import actionlog.models
import actionlog.constants

import reports.models

import zweiapi.views
import zemauth.models


class CampaignStatusTest(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def test_update_status(self):
        zwei_response_data = {
            'status': 'success',
            'data': {
                'daily_budget_cc': 100000,
                'state': 1,
                'cpc_cc': 3000
            }
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)

        current_state = dash.models.AdGroupSourceState.objects \
            .filter(ad_group_source=ad_group_source).latest('created_dt')

        action_log = actionlog.models.ActionLog(
            action=actionlog.constants.Action.FETCH_CAMPAIGN_STATUS,
            state=actionlog.constants.ActionState.WAITING,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
        )
        action_log.save()

        response = self.client.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )
        self.assertEqual(response.status_code, 200)

        latest_state = dash.models.AdGroupSourceState.objects \
            .filter(ad_group_source=ad_group_source).latest('created_dt')

        self.assertNotEqual(latest_state, current_state)


class GetContentAdStatusTest(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def test_get_content_ad_status(self):
        zwei_response_data = {
            'status': 'success',
            'data': [{
                'id': '987654321',
                'state': dash.constants.ContentAdSourceState.INACTIVE,
                'submission_status': dash.constants.ContentAdSubmissionStatus.APPROVED
            }]
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)
        content_ad_source = dash.models.ContentAdSource.objects.get(id=1)

        self.assertEqual(
            content_ad_source.source_state,
            dash.constants.ContentAdSourceState.ACTIVE
        )

        self.assertEqual(
            content_ad_source.submission_status,
            dash.constants.ContentAdSubmissionStatus.PENDING
        )

        action_log = actionlog.models.ActionLog(
            action=actionlog.constants.Action.GET_CONTENT_AD_STATUS,
            state=actionlog.constants.ActionState.WAITING,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
            content_ad_source=content_ad_source
        )
        action_log.save()

        response = self.client.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )
        self.assertEqual(response.status_code, 200)

        content_ad_source = dash.models.ContentAdSource.objects.get(id=1)
        self.assertEqual(
            content_ad_source.source_state,
            dash.constants.ContentAdSourceState.INACTIVE
        )

        self.assertEqual(
            content_ad_source.submission_status,
            dash.constants.ContentAdSubmissionStatus.APPROVED
        )


class UpdateContentAdTest(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def test_update_content_ad(self):
        zwei_response_data = {
            'status': 'success',
            'data': {
                'source_state': dash.constants.ContentAdSourceState.INACTIVE,
                'submission_status': dash.constants.ContentAdSubmissionStatus.APPROVED
            }
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)
        content_ad_source = dash.models.ContentAdSource.objects.get(id=1)

        self.assertEqual(
            content_ad_source.source_state,
            dash.constants.ContentAdSourceState.ACTIVE
        )

        self.assertEqual(
            content_ad_source.submission_status,
            dash.constants.ContentAdSubmissionStatus.PENDING
        )

        action_log = actionlog.models.ActionLog(
            action=actionlog.constants.Action.UPDATE_CONTENT_AD,
            state=actionlog.constants.ActionState.WAITING,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
            content_ad_source=content_ad_source
        )
        action_log.save()

        response = self.client.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )
        self.assertEqual(response.status_code, 200)

        content_ad_source = dash.models.ContentAdSource.objects.get(id=1)
        self.assertEqual(
            content_ad_source.source_state,
            dash.constants.ContentAdSourceState.INACTIVE
        )

        self.assertEqual(
            content_ad_source.submission_status,
            dash.constants.ContentAdSubmissionStatus.APPROVED
        )


class TestUpdateLastSuccessfulSync(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = zemauth.models.User(id=1)

    def test_update_last_successful_sync_fetch_reports_successful_order(self):
        action = actionlog.models.ActionLog.objects.get(pk=1)

        zweiapi.views._update_last_successful_sync_dt(action, self.request)

        ad_group_source = dash.models.AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T10:00:00')

    def test_update_last_successful_sync_fetch_status_successful_order(self):
        action = actionlog.models.ActionLog.objects.get(pk=5)

        zweiapi.views._update_last_successful_sync_dt(action, self.request)

        ad_group_source = dash.models.AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T10:00:00')

    def test_update_last_successful_sync_fetch_reports_waiting_action_in_order(self):
        action = actionlog.models.ActionLog.objects.get(pk=4)

        zweiapi.views._update_last_successful_sync_dt(action, self.request)

        ad_group_source = dash.models.AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T06:00:00')

    def test_update_last_successful_sync_fetch_status_waiting_action_in_order(self):
        action = actionlog.models.ActionLog.objects.get(pk=6)

        zweiapi.views._update_last_successful_sync_dt(action, self.request)

        ad_group_source = dash.models.AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T10:00:00')


class FetchReportsTestCase(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def test_fetch_reports(self):
        article_row = {
            'title': 'Article 1',
            'url': 'http://example.com',
            'impressions': 50,
            'clicks': 2,
            'cost_cc': 2800
        }
        zwei_response_data = {
            'status': 'success',
            'data': [article_row]
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)
        response, action_log = self._execute_action(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            actionlog.models.ActionLog.objects.get(id=action_log.id).state, actionlog.constants.ActionState.SUCCESS
        )
        self._assert_article_stats(ad_group_source, article_row)

    @override_settings(USE_HASH_CACHE=True)
    def test_fetch_reports_hash_cache(self):
        zweiapi.views.cache.clear()

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'), None)

        article_row = {
            'title': 'Article 1',
            'url': 'http://example.com',
            'impressions': 50,
            'clicks': 2,
            'cost_cc': 2800
        }
        zwei_response_data = {
            'status': 'success',
            'data': [article_row]
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)
        response, action_log = self._execute_action(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            actionlog.models.ActionLog.objects.get(id=action_log.id).state, actionlog.constants.ActionState.SUCCESS
        )
        self._assert_article_stats(ad_group_source, article_row)

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            '7a97d7b612f435a2dba269614e90e3ac'
        )

    @override_settings(USE_HASH_CACHE=True)
    def test_fetch_reports_hash_cache_changed_data(self):
        zweiapi.views.cache.clear()
        zweiapi.views.cache.set('fetch_reports_response_hash_1_1_2014-07-01', '7a97d7b612f435a2dba269614e90e3ac')

        article_row = {
            'title': 'Article 1',
            'url': 'http://example.com',
            'impressions': 50,
            'clicks': 2,
            'cost_cc': 2800
        }
        zwei_response_data = {
            'status': 'success',
            'data': [article_row]
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)
        article_row['title'] = 'Article 2'

        response, action_log = self._execute_action(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            actionlog.models.ActionLog.objects.get(id=action_log.id).state, actionlog.constants.ActionState.SUCCESS
        )
        self._assert_article_stats(ad_group_source, article_row)

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            'c1cbb0b3e637466d86d39026d93f0772'
        )

    @override_settings(USE_HASH_CACHE=True)
    def test_fetch_reports_hash_cache_no_change(self):
        zweiapi.views.cache.clear()
        zweiapi.views.cache.set('fetch_reports_response_hash_1_1_2014-07-01', '7a97d7b612f435a2dba269614e90e3ac')

        article_row = {
            'title': 'Article 1',
            'url': 'http://example.com',
            'impressions': 50,
            'clicks': 2,
            'cost_cc': 2800
        }
        zwei_response_data = {
            'status': 'success',
            'data': [article_row]
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)
        response, action_log = self._execute_action(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            actionlog.models.ActionLog.objects.get(id=action_log.id).state, actionlog.constants.ActionState.SUCCESS
        )
        self.assertFalse(
            dash.models.Article.objects.filter(title=article_row['title'], url=article_row['url']).exists()
        )

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            '7a97d7b612f435a2dba269614e90e3ac'
        )

    @override_settings(USE_HASH_CACHE=False)
    def test_fetch_reports_invalid_empty_rows(self):
        zwei_response_data = {
            'status': 'success',
            'data': []
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)
        reports.models.ArticleStats.objects.create(
            ad_group=ad_group_source.ad_group,
            source=ad_group_source.source,
            article_id=1,
            datetime=datetime.datetime(2014, 7, 1),
            has_traffic_metrics=1,
        )

        response, action_log = self._execute_action(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            actionlog.models.ActionLog.objects.get(id=action_log.id).state, actionlog.constants.ActionState.FAILED
        )

    @override_settings(USE_HASH_CACHE=True)
    def test_fetch_reports_invalid_empty_rows_with_cache(self):
        zweiapi.views.cache.clear()
        zweiapi.views.cache.set('fetch_reports_response_hash_1_1_2014-07-01', '7a97d7b612f435a2dba269614e90e3ac')

        zwei_response_data = {
            'status': 'success',
            'data': []
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)
        reports.models.ArticleStats.objects.create(
            ad_group=ad_group_source.ad_group,
            source=ad_group_source.source,
            article_id=1,
            datetime=datetime.datetime(2014, 7, 1),
            has_traffic_metrics=1,
        )

        response, action_log = self._execute_action(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            actionlog.models.ActionLog.objects.get(id=action_log.id).state, actionlog.constants.ActionState.FAILED
        )

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            '7a97d7b612f435a2dba269614e90e3ac'
        )

    def _assert_article_stats(self, ad_group_source, article_dict):
        article = dash.models.Article.objects.get(title=article_dict['title'], url=article_dict['url'])
        article_stats = reports.models.ArticleStats.objects.get(
            article=article,
            ad_group=ad_group_source.ad_group,
            source=ad_group_source.source
        )

        self.assertEqual(article_stats.impressions, article_dict['impressions'])
        self.assertEqual(article_stats.clicks, article_dict['clicks'])
        self.assertEqual(article_stats.cost_cc, article_dict['cost_cc'])

    def _execute_action(self, ad_group_source, date, zwei_response_data):
        action_log = actionlog.models.ActionLog(
            action=actionlog.constants.Action.FETCH_REPORTS,
            state=actionlog.constants.ActionState.WAITING,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
            payload={
                'action': actionlog.constants.Action.FETCH_REPORTS,
                'source': ad_group_source.source.source_type.type,
                'args': {
                    'partner_campaign_id': '"[fake]"',
                    'date': date
                },
            }
        )

        action_log.save()

        return self.client.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        ), action_log
