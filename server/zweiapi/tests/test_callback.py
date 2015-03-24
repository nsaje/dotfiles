import datetime
import json

from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse

import dash.constants
from dash.models import AdGroupSource, Article, AdGroupSourceState, ContentAdSource
from actionlog.models import ActionLog
from actionlog import constants
from reports.models import ArticleStats
from zweiapi import views


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

        ad_group_source = AdGroupSource.objects.get(id=1)

        current_state = AdGroupSourceState.objects \
            .filter(ad_group_source=ad_group_source).latest('created_dt')

        action_log = ActionLog(
            action=constants.Action.FETCH_CAMPAIGN_STATUS,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
        )
        action_log.save()

        response = self.client.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )
        self.assertEqual(response.status_code, 200)

        latest_state = AdGroupSourceState.objects \
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

        ad_group_source = AdGroupSource.objects.get(id=1)
        content_ad_source = ContentAdSource.objects.get(id=1)

        self.assertEqual(
            content_ad_source.source_state,
            dash.constants.ContentAdSourceState.ACTIVE
        )

        self.assertEqual(
            content_ad_source.submission_status,
            dash.constants.ContentAdSubmissionStatus.PENDING
        )

        action_log = ActionLog(
            action=constants.Action.GET_CONTENT_AD_STATUS,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.AUTOMATIC,
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

        content_ad_source = ContentAdSource.objects.get(id=1)
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

        ad_group_source = AdGroupSource.objects.get(id=1)
        content_ad_source = ContentAdSource.objects.get(id=1)

        self.assertEqual(
            content_ad_source.source_state,
            dash.constants.ContentAdSourceState.ACTIVE
        )

        self.assertEqual(
            content_ad_source.submission_status,
            dash.constants.ContentAdSubmissionStatus.PENDING
        )

        action_log = ActionLog(
            action=constants.Action.UPDATE_CONTENT_AD,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.AUTOMATIC,
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

        content_ad_source = ContentAdSource.objects.get(id=1)
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

    def test_update_last_successful_sync_fetch_reports_successful_order(self):
        action = ActionLog.objects.get(pk=1)

        views._update_last_successful_sync_dt(action)

        ad_group_source = AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T10:00:00')

    def test_update_last_successful_sync_fetch_status_successful_order(self):
        action = ActionLog.objects.get(pk=5)

        views._update_last_successful_sync_dt(action)

        ad_group_source = AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T10:00:00')

    def test_update_last_successful_sync_fetch_reports_waiting_action_in_order(self):
        action = ActionLog.objects.get(pk=4)

        views._update_last_successful_sync_dt(action)

        ad_group_source = AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T06:00:00')

    def test_update_last_successful_sync_fetch_status_waiting_action_in_order(self):
        action = ActionLog.objects.get(pk=6)

        views._update_last_successful_sync_dt(action)

        ad_group_source = AdGroupSource.objects.get(pk=1)
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

        ad_group_source = AdGroupSource.objects.get(id=1)
        response = self._executeAction(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self._assertArticleStats(ad_group_source, article_row)

    @override_settings(USE_HASH_CACHE=True)
    def test_fetch_reports_hash_cache(self):
        views.cache.clear()

        self.assertEqual(
            views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'), None)

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

        ad_group_source = AdGroupSource.objects.get(id=1)
        response = self._executeAction(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self._assertArticleStats(ad_group_source, article_row)

        self.assertEqual(
            views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            '7a97d7b612f435a2dba269614e90e3ac'
        )

    @override_settings(USE_HASH_CACHE=True)
    def test_fetch_reports_hash_cache_changed_data(self):
        views.cache.clear()
        views.cache.set('fetch_reports_response_hash_1_1_2014-07-01', '7a97d7b612f435a2dba269614e90e3ac')

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

        ad_group_source = AdGroupSource.objects.get(id=1)
        article_row['title'] = 'Article 2'

        response = self._executeAction(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self._assertArticleStats(ad_group_source, article_row)

        self.assertEqual(
            views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            'c1cbb0b3e637466d86d39026d93f0772'
        )

    @override_settings(USE_HASH_CACHE=True)
    def test_fetch_reports_hash_cache_no_change(self):
        views.cache.clear()
        views.cache.set('fetch_reports_response_hash_1_1_2014-07-01', '7a97d7b612f435a2dba269614e90e3ac')

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

        ad_group_source = AdGroupSource.objects.get(id=1)
        response = self._executeAction(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)

        self.assertFalse(Article.objects.filter(title=article_row['title'], url=article_row['url']).exists())

        self.assertEqual(
            views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            '7a97d7b612f435a2dba269614e90e3ac'
        )

    def _assertArticleStats(self, ad_group_source, article_dict):
        article = Article.objects.get(title=article_dict['title'], url=article_dict['url'])
        article_stats = ArticleStats.objects.get(
            article=article,
            ad_group=ad_group_source.ad_group,
            source=ad_group_source.source
        )

        self.assertEqual(article_stats.impressions, article_dict['impressions'])
        self.assertEqual(article_stats.clicks, article_dict['clicks'])
        self.assertEqual(article_stats.cost_cc, article_dict['cost_cc'])

    def _executeAction(self, ad_group_source, date, zwei_response_data):
        action_log = ActionLog(
            action=constants.Action.FETCH_REPORTS,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
            payload={
                'action': constants.Action.FETCH_REPORTS,
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
        )
