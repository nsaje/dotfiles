import datetime
import json
import mock

from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.test.client import Client

from dash.models import AdGroupSource, Article, AdGroupSourceState
from actionlog.models import ActionLog
from actionlog import constants
from reports.models import ArticleStats
from zweiapi import views


class CampaignStatusTest(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def setUp(self):
        self.factory = RequestFactory()

    @mock.patch('utils.request_signer.verify_wsgi_request')
    def test_update_status(self, _):
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

        c = Client()
        response = c.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )
        self.assertEqual(response.status_code, 200)

        latest_state = AdGroupSourceState.objects \
            .filter(ad_group_source=ad_group_source).latest('created_dt')

        self.assertNotEqual(latest_state, current_state)


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

    def setUp(self):
        self.factory = RequestFactory()

    @mock.patch('utils.request_signer.verify_wsgi_request')
    def test_fetch_reports(self, _):
        article_row = {
            'title': 'Article 1',
            'url': 'http://example.com',
            'impressions': 50,
            'clicks': 2,
            'cost_cc': 2800
        }
        zwei_response_data = {
            'status': 'success',
            'data': [[["fake"], [article_row]]]
        }

        ad_group_source = AdGroupSource.objects.get(id=1)
        response = self._executeAction(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self._assertArticleStats(ad_group_source, article_row)

    @override_settings(USE_HASH_CACHE=True)
    @mock.patch('utils.request_signer.verify_wsgi_request')
    def test_fetch_reports_hash_cache(self, _):
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
            'data': [[["fake"], [article_row]]]
        }

        ad_group_source = AdGroupSource.objects.get(id=1)
        response = self._executeAction(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self._assertArticleStats(ad_group_source, article_row)

        self.assertEqual(
            views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            '1d46fd9f369f21627f7a1ecaf11dbfc6'
        )

        # again with different data
        article_row['title'] = 'Article 2'

        response = self._executeAction(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)
        self._assertArticleStats(ad_group_source, article_row)

        self.assertEqual(
            views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            'a48a540ed57fd4bb0fdb36a6df6fef0a'
        )

    @override_settings(USE_HASH_CACHE=True)
    @mock.patch('utils.request_signer.verify_wsgi_request')
    def test_fetch_reports_hash_cache_no_change(self, _):
        views.cache.clear()
        views.cache.set('fetch_reports_response_hash_1_1_2014-07-01', '1d46fd9f369f21627f7a1ecaf11dbfc6')

        article_row = {
            'title': 'Article 1',
            'url': 'http://example.com',
            'impressions': 50,
            'clicks': 2,
            'cost_cc': 2800
        }
        zwei_response_data = {
            'status': 'success',
            'data': [[["fake"], [article_row]]]
        }

        ad_group_source = AdGroupSource.objects.get(id=1)
        response = self._executeAction(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(response.status_code, 200)

        self.assertFalse(Article.objects.filter(title=article_row['title'], url=article_row['url']).exists())

        self.assertEqual(
            views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'),
            '1d46fd9f369f21627f7a1ecaf11dbfc6'
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

        c = Client()
        return c.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )
