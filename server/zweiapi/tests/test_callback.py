import datetime
import json
import mock

from mock import patch
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

    def setUp(self):
        ad_group_settings = dash.models.AdGroup.objects.get(pk=1).get_current_settings()
        ad_group_settings.state = dash.constants.AdGroupSettingsState.ACTIVE
        ad_group_settings.save(None)

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

        content_ad_source.content_ad.state = dash.constants.ContentAdSourceState.INACTIVE
        content_ad_source.content_ad.save()

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

    @mock.patch('dash.views.views.actionlog.zwei_actions.send')
    def test_get_content_ad_status_with_status_sync(self, mock_send):
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

        content_ad_source.content_ad.state = dash.constants.ContentAdSourceState.ACTIVE
        content_ad_source.content_ad.save()

        self.assertEqual(
            content_ad_source.source_state,
            dash.constants.ContentAdSourceState.ACTIVE
        )

        action_log = actionlog.models.ActionLog(
            action=actionlog.constants.Action.GET_CONTENT_AD_STATUS,
            state=actionlog.constants.ActionState.WAITING,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
            content_ad_source=content_ad_source
        )
        action_log.save()

        self.assertTrue(
            'args' not in actionlog.models.ActionLog.objects.all().order_by('-created_dt')[0].payload
        )

        response = self.client.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )
        self.assertEqual(response.status_code, 200)

        content_ad_source = dash.models.ContentAdSource.objects.get(id=1)

        # should update source state and create an action that syncs the state
        self.assertEqual(
            content_ad_source.source_state,
            dash.constants.ContentAdSourceState.INACTIVE
        )

        action = actionlog.models.ActionLog.objects.all().\
                 order_by('-created_dt')[0]

        self.assertEqual(action.payload['args']['changes'], {'state': dash.constants.ContentAdSourceState.ACTIVE})

        mock_send.assert_called_with([action])


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


class CreateCampaignManualActionsTest(TestCase):
    fixtures = ['test_zwei_api.yaml']

    def setUp(self):
        password = 'secret'
        user = zemauth.models.User.objects.get(pk=1)

        self.request = HttpRequest()
        self.request.user = user
        self.client.login(username=user.email, password=password)

    def _setup_ad_group_source(
            self,
            ad_group_source,
            target_regions=None,
            available_actions=None,
            retargeting_ad_groups=None
        ):
        if available_actions:
            ad_group_source.source.source_type.available_actions.extend(available_actions)
            ad_group_source.source.source_type.save()

        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        ad_group_settings.target_regions = target_regions
        ad_group_settings.retargeting_ad_groups = retargeting_ad_groups
        ad_group_settings.save(self.request)

    def _fire_campaign_creation_callback(self, ad_group_source):
        # setup actionlog
        action_log = actionlog.models.ActionLog(
            action=actionlog.constants.Action.CREATE_CAMPAIGN,
            state=actionlog.constants.ActionState.WAITING,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source
        )
        action_log.save()

        zwei_response_data = {
            'status': 'success',
            'data': {
                'source_campaign_key': 'asd'
            }
        }

        response = self.client.post(
            reverse('api.zwei_callback', kwargs={'action_id': action_log.id}),
            content_type='application/json',
            data=json.dumps(zwei_response_data)
        )
        self.assertEqual(response.status_code, 200)

    def _get_created_manual_actions(self, ad_group_source):
        return actionlog.models.ActionLog.objects.filter(
            action=actionlog.constants.Action.SET_PROPERTY,
            ad_group_source=ad_group_source,
            action_type=actionlog.constants.ActionType.MANUAL
        )

    @patch('dash.api.order_additional_updates_after_campaign_creation')
    def test_order_additional_updates_after_campaign_creation_fires(self, mock_order_additional_updates):
        ad_group_source = dash.models.AdGroupSource.objects.get(id=3)

        self._fire_campaign_creation_callback(ad_group_source)

        mock_order_additional_updates.assert_called_with(ad_group_source, request=None)

    @patch('dash.consistency.SettingsStateConsistence')
    @patch('actionlog.api.set_ad_group_source_settings')
    @patch('actionlog.zwei_actions.send')
    def test_set_ad_group_source_settings_fires(self, mock_send, mock_set_ad_group_source_settings, mock_consistence):
        ad_group_source = dash.models.AdGroupSource.objects.get(id=3)

        changes = {
            'daily_budget_cc': 123
        }

        mock_consistence().get_needed_state_updates.return_value = changes

        self._fire_campaign_creation_callback(ad_group_source)

        mock_set_ad_group_source_settings.assert_called_with(changes, ad_group_source, request=None, send=False)
        self.assertTrue(mock_send.called)

    def test_manual_update_after_campaign_creation_manual_dma_targeting(self):
        ad_group_source = dash.models.AdGroupSource.objects.get(id=3)

        self._setup_ad_group_source(
            ad_group_source,
            ['GB', '693'],
            [
                dash.constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_MANUAL,
                dash.constants.SourceAction.CAN_MODIFY_COUNTRY_TARGETING
            ])
        self._fire_campaign_creation_callback(ad_group_source)

        manual_actions = self._get_created_manual_actions(ad_group_source)

        # should create manual actions
        self.assertEqual(len(manual_actions), 1)
        self.assertEqual('target_regions', manual_actions[0].payload['property'])

    def test_manual_update_after_campaign_creation_retargeting(self):
        ad_group_source = dash.models.AdGroupSource.objects.get(id=3)
        ad_group_source.source.supports_retargeting_manually = True
        ad_group_source.source.save()

        self._setup_ad_group_source(
            ad_group_source,
            retargeting_ad_groups=[1]
            )

        self._fire_campaign_creation_callback(ad_group_source)

        manual_actions = self._get_created_manual_actions(ad_group_source)
        # should create manual actions
        self.assertEqual(len(manual_actions), 1)
        self.assertEqual('retargeting_ad_groups', manual_actions[0].payload['property'])


class SubmitAdGroupTest(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def test_valid(self):
        zwei_response_data = {
            'status': 'success',
            'data': {
                'source_content_ad_id': '1234567890',
                'submission_status': dash.constants.ContentAdSubmissionStatus.PENDING,
                'submission_errors': None
            }
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=6)
        content_ad_source1 = dash.models.ContentAdSource.objects.get(id=3)
        self.assertEqual(
            content_ad_source1.submission_status,
            dash.constants.ContentAdSubmissionStatus.NOT_SUBMITTED
        )
        self.assertEqual(
            content_ad_source1.source_content_ad_id,
            None
        )

        content_ad_source2 = dash.models.ContentAdSource.objects.get(id=4)
        self.assertEqual(
            content_ad_source2.submission_status,
            dash.constants.ContentAdSubmissionStatus.APPROVED
        )
        self.assertEqual(
            content_ad_source2.source_content_ad_id,
            None
        )

        action_log = actionlog.models.ActionLog(
            action=actionlog.constants.Action.SUBMIT_AD_GROUP,
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

        action_log = actionlog.models.ActionLog.objects.get(id=action_log.id)
        self.assertEqual(
            action_log.state,
            actionlog.constants.ActionState.SUCCESS
        )

        ad_group_source = dash.models.AdGroupSource.objects.get(id=6)
        self.assertEqual(
            ad_group_source.submission_status,
            dash.constants.ContentAdSubmissionStatus.PENDING
        )
        self.assertEqual(
            ad_group_source.source_content_ad_id,
            '1234567890'
        )

        content_ad_source1 = dash.models.ContentAdSource.objects.get(id=3)
        self.assertEqual(
            content_ad_source1.submission_status,
            dash.constants.ContentAdSubmissionStatus.PENDING
        )
        self.assertEqual(
            content_ad_source1.source_content_ad_id,
            '1234567890'
        )

        content_ad_source2 = dash.models.ContentAdSource.objects.get(id=4)
        self.assertEqual(
            content_ad_source2.submission_status,
            dash.constants.ContentAdSubmissionStatus.APPROVED
        )
        self.assertEqual(
            content_ad_source2.source_content_ad_id,
            None
        )

    def test_invalid(self):
        zwei_response_data = {
            'status': 'success',
            'data': {
                'source_content_ad_id': '1234567890',
                'submission_status': dash.constants.ContentAdSubmissionStatus.PENDING,
                'submission_errors': None
            }
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=1)

        action_log = actionlog.models.ActionLog(
            action=actionlog.constants.Action.SUBMIT_AD_GROUP,
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

        action_log = actionlog.models.ActionLog.objects.get(id=action_log.id)
        self.assertEqual(
            action_log.state,
            actionlog.constants.ActionState.FAILED
        )


class TestUpdateLastSuccessfulSync(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = zemauth.models.User(id=1)

    def test_update_last_successful_sync_fetch_reports_successful_order(self):
        action1 = actionlog.models.ActionLog.objects.get(pk=1)
        action2 = actionlog.models.ActionLog.objects.get(pk=5)

        zweiapi.views._update_last_successful_sync_dt(action1, self.request)
        zweiapi.views._update_last_successful_sync_dt(action2, self.request)

        ad_group_source = dash.models.AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T10:00:00')

    def test_update_last_successful_sync_fetch_status_successful_order(self):
        action1 = actionlog.models.ActionLog.objects.get(pk=1)
        action2 = actionlog.models.ActionLog.objects.get(pk=5)

        zweiapi.views._update_last_successful_sync_dt(action2, self.request)
        zweiapi.views._update_last_successful_sync_dt(action1, self.request)

        ad_group_source = dash.models.AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T10:00:00')

    def test_update_last_successful_sync_fetch_reports_waiting_action_in_order(self):
        action = actionlog.models.ActionLog.objects.get(pk=4)

        zweiapi.views._update_last_successful_sync_dt(action, self.request)

        ad_group_source = dash.models.AdGroupSource.objects.get(pk=1)
        self.assertEqual(ad_group_source.last_successful_sync_dt.isoformat(), '2014-07-03T06:00:00')


class FetchReportsTestCase(TestCase):

    fixtures = ['test_zwei_api.yaml']

    def setUp(self):
        cursor_patcher = patch('reports.redshift.get_cursor')
        self.cursor_mock = cursor_patcher.start()
        self.addCleanup(cursor_patcher.stop)

    @patch('reports.refresh.notify_contentadstats_change', mock.MagicMock())
    def test_fetch_reports(self):
        article_row = {
            'id': '987654321',
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
    @patch('reports.refresh.notify_contentadstats_change', mock.MagicMock())
    def test_fetch_reports_hash_cache(self):
        zweiapi.views.cache.clear()

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01'), None)

        article_row = {
            'id': '987654321',
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
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link'),
            '79753a5d1f7184c4df217733679ce89a'
        )

    @override_settings(USE_HASH_CACHE=True)
    @patch('reports.refresh.notify_contentadstats_change', mock.MagicMock())
    def test_fetch_reports_hash_cache_changed_data(self):
        zweiapi.views.cache.clear()
        zweiapi.views.cache.set('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link', '7a97d7b612f435a2dba269614e90e3ac')

        article_row = {
            'id': '987654321',
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
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link'),
            'cc8a15d36215e9e7bd50dcac5c381289'
        )

    @override_settings(USE_HASH_CACHE=True)
    def test_fetch_reports_hash_cache_no_change(self):
        zweiapi.views.cache.clear()
        zweiapi.views.cache.set('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link', '79753a5d1f7184c4df217733679ce89a')

        article_row = {
            'id': '987654321',
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
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link'),
            '79753a5d1f7184c4df217733679ce89a'
        )

    @override_settings(USE_HASH_CACHE=True)
    @mock.patch('reports.update.stats_update_adgroup_source_traffic')
    def test_cache_not_set_on_adgroup_stats_exception(self, mock_stats_update_adgroup_source_traffic):
        mock_stats_update_adgroup_source_traffic.side_effect = Exception()
        zweiapi.views.cache.clear()

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link'),
            None
        )

        article_row = {
            'id': '987654321',
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

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link'),
            None
        )

    @override_settings(USE_HASH_CACHE=True)
    @mock.patch('reports.update.update_content_ads_source_traffic_stats')
    def test_cache_not_set_on_content_ads_stats_exception(self, mock_update_content_ads_source_traffic_stats):
        mock_update_content_ads_source_traffic_stats.side_effect = Exception()
        zweiapi.views.cache.clear()

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link'),
            None
        )

        article_row = {
            'id': '987654321',
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
        ad_group_source.can_manage_content_ads = True
        ad_group_source.save()

        response, action_log = self._execute_action(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)

        self.assertEqual(
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link'),
            None
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

    @override_settings(USE_HASH_CACHE=False)
    @patch('reports.refresh.notify_contentadstats_change', mock.MagicMock())
    def test_fetch_reports_delete_empty_rows(self):
        zwei_response_data = {
            'status': 'success',
            'data': []
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=3)
        reports.models.ArticleStats.objects.create(
            ad_group=ad_group_source.ad_group,
            source=ad_group_source.source,
            article_id=1,
            datetime=datetime.datetime(2014, 7, 1),
            clicks=8,
            has_traffic_metrics=1,
        )

        response, action_log = self._execute_action(ad_group_source, datetime.date(2014, 7, 1), zwei_response_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            actionlog.models.ActionLog.objects.get(id=action_log.id).state, actionlog.constants.ActionState.SUCCESS
        )

    @override_settings(USE_HASH_CACHE=True)
    def test_fetch_reports_invalid_empty_rows_with_cache(self):
        zweiapi.views.cache.clear()
        zweiapi.views.cache.set('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link', '7a97d7b612f435a2dba269614e90e3ac')

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
            zweiapi.views.cache.get('fetch_reports_response_hash_1_1_2014-07-01_reports_by_link'),
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


class FetchReportsByPublisherTestCase(TestCase):

    fixtures = ['test_zwei_api.yaml', 'test_article_stats_ob.yaml']

    @patch('reports.api_publishers.put_ob_data_to_s3')
    def test_fetch_reports_by_publisher(self, mock_put_to_s3):
        article_row = {
            'url': 'http://money.cnn.com',
            'name': 'Some publisher',
            'clicks': 2,
            'ob_id': 'AABBCCDDEEFF',
        }
        zwei_response_data = {
            'status': 'success',
            'data': [article_row]
        }

        ad_group_source = dash.models.AdGroupSource.objects.get(id=3)
        response, action_log = self._execute_action(ad_group_source, datetime.date(2014, 6, 4), zwei_response_data)
        mock_put_to_s3.assert_called_once_with(datetime.date(2014, 6, 4), ad_group_source.ad_group, [article_row])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            actionlog.models.ActionLog.objects.get(id=action_log.id).state, actionlog.constants.ActionState.SUCCESS
        )

    def _execute_action(self, ad_group_source, date, zwei_response_data):
        action_log = actionlog.models.ActionLog(
            action=actionlog.constants.Action.FETCH_REPORTS_BY_PUBLISHER,
            state=actionlog.constants.ActionState.WAITING,
            action_type=actionlog.constants.ActionType.AUTOMATIC,
            ad_group_source=ad_group_source,
            payload={
                'action': actionlog.constants.Action.FETCH_REPORTS_BY_PUBLISHER,
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
