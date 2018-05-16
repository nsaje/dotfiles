import json
from mock import patch, ANY

from django.core.urlresolvers import reverse
from django.http.request import HttpRequest
from django.test import TestCase, Client, RequestFactory

from dash import api
from dash import constants
from dash import history_helpers
from dash import models
from dash.views import bulk_actions

from zemauth.models import User


class AdGroupSourceStateTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        self.client = Client()
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def _post_source_state(self, ad_group_id, data):
        return self.client.post(
            reverse(
                'ad_group_source_state',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    @patch('dash.legacy.get_updated_ad_group_sources_changes')
    @patch('dash.views.bulk_actions.AdGroupSourceState._check_can_set_state')
    @patch('automation.autopilot.recalculate_budgets_ad_group')
    @patch('utils.k1_helper.update_ad_group')
    def test_post(self, mock_k1_ping, mock_autopilot, mock_check, mock_table_update):
        ad_group_id = 1
        source_id = 1
        maintenance_source_id = 6

        settings = models.AdGroup.objects.get(pk=ad_group_id).get_current_settings().copy_settings()
        settings.retargeting_ad_groups = False
        settings.exclusion_retargeting_ad_groups = False
        settings.audience_targeting = False
        settings.exclusion_audience_targeting = False
        settings.save(None)

        data = {
            'state': constants.AdGroupSourceSettingsState.ACTIVE,
            'selected_ids': [source_id, maintenance_source_id],
        }

        mock_table_update.return_value = {
            'rows': {
                '1': {
                    'cpc': 3,
                },
                '2': {
                    'cpc': 4,
                }
            }
        }

        response = self._post_source_state(ad_group_id, data)

        self.maxDiff = None

        self.assertJSONEqual(response.content, {
            'success': True,
            'data': {
                'rows': [{
                    'breakdownId': '1',
                    'stats': {
                        'state': {
                            'editMessage': 'This source must be managed manually.',
                            'isEditable': False,
                            'value': 1,
                        },
                        'status': {'value': 1},
                        'cpc': {'value': 3},
                    },
                }, {
                    'breakdownId': '2',
                    'stats': {
                        'cpc': {'value': 4},
                    }
                }],
            },
        })

        agss = models.AdGroupSource.objects.get(ad_group_id=ad_group_id, source_id=source_id).get_current_settings()
        self.assertEqual(constants.AdGroupSourceSettingsState.ACTIVE, agss.state)

        adg = models.AdGroup.objects.get(pk=ad_group_id)
        mock_autopilot.assert_called_once_with(adg, send_mail=False)
        self.assertEqual(1, mock_check.call_count)
        self.assertEqual(1, mock_table_update.call_count)

        mock_k1_ping.assert_called_once_with(1, msg='AdGroupSourceState.post')

    @patch('dash.views.helpers.enabling_autopilot_sources_allowed')
    @patch('dash.views.helpers.check_facebook_source')
    @patch('dash.retargeting_helper.can_add_source_with_retargeting')
    def test_check_can_set_state(self, retargeting_mock, facebook_mock, autopilot_check_mock):
        view = bulk_actions.AdGroupSourceState()
        campaign_settings = models.CampaignSettings()
        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_settings = ad_group.get_current_settings()
        ad_group_sources = ad_group.adgroupsource_set.all()
        state = constants.AdGroupSourceSettingsState.ACTIVE

        view._check_can_set_state(campaign_settings, ad_group_settings, ad_group, ad_group_sources, state)

        self.assertEqual(len(ad_group_sources), retargeting_mock.call_count)
        self.assertEqual(len(ad_group_sources), facebook_mock.call_count)
        autopilot_check_mock.assert_called_once_with(
            ad_group,
            ad_group_sources
        )


class AdGroupContentAdArchiveTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_content_ad_archive(self, ad_group_id, data):
        return self.client.post(
            reverse(
                'ad_group_content_ad_archive',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    @patch('utils.email_helper.send_ad_group_notification_email')
    @patch('utils.k1_helper.update_content_ads')
    def test_post(self, mock_k1_ping, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)
        content_ad_id = 2

        data = {
            'selected_ids': [content_ad_id],
        }

        response = self._post_content_ad_archive(ad_group.id, data)
        mock_k1_ping.assert_called_with(1, [content_ad_id], msg='AdGroupContentAdArchive.post')
        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.archived, True)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], [{
            'breakdownId': '2',
            'archived': True,
            'stats': {
                'status': {'value': content_ad.state},
                'state': {'value': content_ad.state},
            },
        }])

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, 'Content ad(s) 2 Archived.')
        hist = history_helpers.get_ad_group_history(ad_group).first()
        self.assertEqual(constants.HistoryActionType.CONTENT_AD_ARCHIVE_RESTORE, hist.action_type)

    @patch('utils.email_helper.send_ad_group_notification_email')
    def test_archive_set_all(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': True,
        }

        response = self._post_content_ad_archive(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        self.assertTrue(all([ad.archived is True for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertCountEqual(
            response_dict['data']['rows'],
            [{
                'breakdownId': str(ad.id),
                'archived': True,
                'stats': {
                    'status': {'value': ad.state},
                    'state': {'value': ad.state},
                },
            } for ad in content_ads],
        )

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('utils.email_helper.send_ad_group_notification_email')
    def test_archive_set_batch(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        batch_id = 2
        content_ads = models.ContentAd.objects.filter(batch__id=batch_id, archived=False)

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': False,
            'select_batch': batch_id,
        }

        response = self._post_content_ad_archive(ad_group.id, payload)

        for content_ad in content_ads:
            content_ad.refresh_from_db()

        self.assertTrue(all([ad.archived is True for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertCountEqual(
            response_dict['data']['rows'],
            [{
                'breakdownId': str(ad.id),
                'archived': True,
                'stats': {
                    'status': {'value': ad.state},
                    'state': {'value': ad.state},
                },
            } for ad in content_ads],
        )

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('utils.email_helper.send_ad_group_notification_email')
    def test_archive_pause_active_before_archiving(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id, archived=False)
        self.assertGreater(len(content_ads), 0)
        self.assertFalse(all([ad.state == constants.ContentAdSourceState.INACTIVE for ad in content_ads]))

        active_count = len([ad for ad in content_ads if ad.state == constants.ContentAdSourceState.ACTIVE])
        archived_count = len(content_ads)

        payload = {
            'select_all': True
        }

        response = self._post_content_ad_archive(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        self.assertTrue(all([ad.state == constants.ContentAdSourceState.INACTIVE and ad.archived
                             for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['activeCount'], active_count)
        self.assertEqual(response_dict['data']['archivedCount'], archived_count)

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, 'Content ad(s) 1, 2 Archived.')

    @patch('utils.email_helper.send_ad_group_notification_email')
    def test_content_ad_ids_validation_error(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)

        response = self._post_content_ad_archive(ad_group.id, {'selected_ids': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

        self.assertFalse(mock_send_mail.called)

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, True, request)

        hist = history_helpers.get_ad_group_history(ad_group).first()
        self.assertIsNotNone(hist.created_by)
        self.assertEqual(constants.HistoryActionType.CONTENT_AD_ARCHIVE_RESTORE, hist.action_type)
        self.assertEqual(hist.changes_text, 'Content ad(s) 1, 2, 3 Archived.')

    def test_add_to_history_shorten(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)
        content_ads = list(content_ads) * 4  # need more than 10 ads

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, True, request)

        hist = history_helpers.get_ad_group_history(ad_group).first()
        self.assertIsNotNone(hist.created_by)
        self.assertEqual(constants.HistoryActionType.CONTENT_AD_ARCHIVE_RESTORE, hist.action_type)
        self.assertEqual(
            hist.changes_text,
            'Content ad(s) 1, 2, 3, 1, 2, 3, 1, 2, 3, 1 and 2 more Archived.'
        )


class AdGroupContentAdRestore(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_content_ad_restore(self, ad_group_id, data):
        return self.client.post(
            reverse(
                'ad_group_content_ad_restore',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    @patch('utils.email_helper.send_ad_group_notification_email')
    @patch('utils.k1_helper.update_content_ads')
    def test_post(self, mock_k1_ping, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)
        content_ad_id = 2

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        content_ad.archived = True
        content_ad.save()

        data = {
            'selected_ids': [content_ad_id],
        }

        response = self._post_content_ad_restore(ad_group.id, data)
        mock_k1_ping.assert_called_with(1, [2], msg='AdGroupContentAdRestore.post')

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.archived, False)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(
            response_dict['data']['rows'],
            [{
                'breakdownId': '2',
                'archived': False,
                'stats': {
                    'status': {'value': content_ad.state},
                    'state': {'value': content_ad.state},
                },
            }],
        )

        mock_send_mail.assert_called_with(
            ad_group, response.wsgi_request, 'Content ad(s) 2 Restored.')
        hist = history_helpers.get_ad_group_history(ad_group).first()
        self.assertEqual(constants.HistoryActionType.CONTENT_AD_ARCHIVE_RESTORE, hist.action_type)

    @patch('utils.email_helper.send_ad_group_notification_email')
    def test_restore_set_all(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        for ad in content_ads:
            ad.archived = True
            ad.save()

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': True,
        }

        response = self._post_content_ad_restore(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        self.assertTrue(all([ad.archived is False for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertCountEqual(
            response_dict['data']['rows'],
            [{
                'breakdownId': str(ad.id),
                'archived': False,
                'stats': {
                    'status': {'value': ad.state},
                    'state': {'value': ad.state},
                },
            } for ad in content_ads],
        )

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('utils.email_helper.send_ad_group_notification_email')
    def test_archive_set_batch(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        batch_id = 2
        content_ads = models.ContentAd.objects.filter(batch__id=batch_id)
        for ad in content_ads:
            ad.archived = True
            ad.save()

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': False,
            'select_batch': batch_id,
        }

        response = self._post_content_ad_restore(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(batch__id=batch_id)
        self.assertTrue(all([ad.archived is False for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertCountEqual(
            response_dict['data']['rows'],
            [{
                'breakdownId': str(ad.id),
                'archived': False,
                'stats': {
                    'status': {'value': ad.state},
                    'state': {'value': ad.state},
                },
            } for ad in content_ads],
        )

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('utils.email_helper.send_ad_group_notification_email')
    def test_restore_success_when_all_restored(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=2)
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)

        self.assertGreater(len(content_ads), 0)
        self.assertTrue(all([not ad.archived for ad in content_ads]))

        payload = {
            'select_all': True
        }

        response = self._post_content_ad_restore(ad_group.id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group.id)
        self.assertFalse(all([ad.archived for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertTrue(response_dict['success'])

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request, ANY)

    @patch('utils.email_helper.send_ad_group_notification_email')
    def test_content_ad_ids_validation_error(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)

        response = self._post_content_ad_restore(ad_group.id, {'selected_ids': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

        self.assertFalse(mock_send_mail.called)

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, False, request)

        hist = history_helpers.get_ad_group_history(ad_group).first()
        self.assertEqual(constants.HistoryActionType.CONTENT_AD_ARCHIVE_RESTORE, hist.action_type)
        self.assertEqual(hist.changes_text, 'Content ad(s) 1, 2, 3 Restored.')

    def test_add_to_history_shorten(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)
        content_ads = list(content_ads) * 4  # need more than 10 ads

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history_and_notify(ad_group, content_ads, False, request)

        hist = history_helpers.get_ad_group_history(ad_group).first()
        self.assertIsNotNone(hist.created_by)
        self.assertEqual(constants.HistoryActionType.CONTENT_AD_ARCHIVE_RESTORE, hist.action_type)
        self.assertEqual(
            hist.changes_text,
            'Content ad(s) 1, 2, 3, 1, 2, 3, 1, 2, 3, 1 and 2 more Restored.'
        )


class AdGroupContentAdStateTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_content_ad_state(self, ad_group_id, data):
        return self.client.post(
            reverse(
                'ad_group_content_ad_state',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    @patch('utils.k1_helper.update_content_ads')
    def test_post(self, mock_k1_ping):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        ad_group_id = 1
        content_ad_id = 1

        data = {
            'state': constants.ContentAdSourceState.INACTIVE,
            'selected_ids': [content_ad_id],
        }

        response = self._post_content_ad_state(ad_group_id, data)

        mock_k1_ping.assert_called_with(1, [1], msg='AdGroupContentAdState.post')

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.state, constants.ContentAdSourceState.INACTIVE)

        content_ad_sources = models.ContentAdSource.objects.filter(content_ad=content_ad)
        self.assertEqual(len(content_ad_sources), 3)

        for content_ad_source in content_ad_sources:
            self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.INACTIVE)

        self.assertJSONEqual(response.content, {
            'success': True,
            'data': {
                'rows': [{
                    'breakdownId': str(content_ad_id),
                    'stats': {
                        'state': {'value': constants.ContentAdSourceState.INACTIVE},
                        'status': {'value': constants.ContentAdSourceState.INACTIVE},
                    }
                }]
            }
        })

        hist = history_helpers.get_ad_group_history(models.AdGroup.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONTENT_AD_STATE_CHANGE, hist.action_type)

    def test_state_set_all(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        content_ads = models.ContentAd.objects.filter(ad_group__id=1)
        self.assertGreater(len(content_ads), 0)
        self.assertFalse(all([ad.state == constants.ContentAdSourceState.INACTIVE for ad in content_ads]))

        payload = {
            'select_all': True,
            'state': constants.ContentAdSourceState.INACTIVE,
        }

        self._post_content_ad_state(1, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=1)
        self.assertTrue(all([ad.state == constants.ContentAdSourceState.INACTIVE for ad in content_ads]))

    def test_state_set_batch(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        content_ads = models.ContentAd.objects.filter(batch__id=1)
        self.assertGreater(len(content_ads), 0)
        self.assertFalse(all([ad.state == constants.ContentAdSourceState.INACTIVE
                              for ad in content_ads]))

        payload = {
            'select_all': False,
            'select_batch': 1,
            'state': constants.ContentAdSourceState.INACTIVE,
        }

        self._post_content_ad_state(1, payload)

        content_ads = models.ContentAd.objects.filter(batch__id=1)
        self.assertTrue(all([ad.state == constants.ContentAdSourceState.INACTIVE
                             for ad in content_ads]))

    def test_dont_set_state_on_archived_ads(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        archived_ad = models.ContentAd.objects.get(pk=3)
        archived_ad.archived = True
        archived_ad.save()
        self.assertEqual(archived_ad.state, constants.ContentAdSourceState.INACTIVE)

        restored_ad = models.ContentAd.objects.get(pk=4)
        self.assertFalse(restored_ad.archived)
        self.assertEqual(archived_ad.state, constants.ContentAdSourceState.INACTIVE)

        payload = {
            'selected_ids': [archived_ad.id, restored_ad.id],
            'state': constants.ContentAdSourceState.ACTIVE,
        }

        self._post_content_ad_state(2, payload)

        archived_ad.refresh_from_db()
        self.assertEqual(archived_ad.state, constants.ContentAdSourceState.INACTIVE)

        restored_ad.refresh_from_db()
        self.assertEqual(restored_ad.state, constants.ContentAdSourceState.ACTIVE)

    def test_update_content_ads(self):
        content_ad = models.ContentAd.objects.get(pk=1)
        state = constants.ContentAdSourceState.INACTIVE
        request = None

        api.update_content_ads_state([content_ad], state, request)

        content_ad.refresh_from_db()

        self.assertEqual(content_ad.state, constants.ContentAdSourceState.INACTIVE)

        for content_ad_source in content_ad.contentadsource_set.all():
            self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.INACTIVE)

    def test_get_content_ad_ids_validation_error(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')
        response = self._post_content_ad_state(1, {'selected_ids': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        state = constants.ContentAdSourceState.ACTIVE

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_state_change_to_history_and_notify(ad_group, content_ads, state, request)

        hist = history_helpers.get_ad_group_history(ad_group).first()
        self.assertIsNotNone(hist.created_by)
        self.assertEqual(constants.HistoryActionType.CONTENT_AD_STATE_CHANGE, hist.action_type)
        self.assertEqual('Content ad(s) 1, 2, 3 set to Enabled.', hist.changes_text)

    def test_add_to_history_shorten(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)
        content_ads = list(content_ads) * 4  # need more than 10 ads

        state = constants.ContentAdSourceState.ACTIVE

        request = HttpRequest()
        request.META['SERVER_NAME'] = 'testname'
        request.META['SERVER_PORT'] = 1234
        request.user = User(id=1)

        api.add_content_ads_state_change_to_history_and_notify(ad_group, content_ads, state, request)

        hist = history_helpers.get_ad_group_history(ad_group).first()
        self.assertIsNotNone(hist.created_by)
        self.assertEqual(constants.HistoryActionType.CONTENT_AD_STATE_CHANGE, hist.action_type)
        self.assertEqual(
            hist.changes_text,
            'Content ad(s) 1, 2, 3, 1, 2, 3, 1, 2, 3, 1 and 2 more set to Enabled.'
        )


class AdGroupContentAdCSVTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_get_all(self):
        data = {
            'select_all': True
        }

        response = self._get_csv_from_server(data)

        expected_content = b'\r\n'.join([
            b'"URL","Title","Image URL","Image crop","Display URL","Brand name","Call to action","Description","Primary impression tracker URL","Secondary impression tracker URL","Label"',  # noqa
            b'"http://testurl.com","Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1","123456789.jpg","center","example.com","Example","Call to action","Example description","http://testurl.com","http://testurl2.com",""',  # noqa
            b'"http://testurl.com","Test Article with no content_ad_sources 1","123456789.jpg","center","example.com","Example","Call to action","Example description","","",""'  # noqa
        ]) + b'\r\n'

        self.assertEqual(response.content, expected_content)

    def test_get_all_include_archived(self):
        data = {
            'select_all': True,
            'archived': 'true'
        }

        response = self._get_csv_from_server(data)

        expected_content = b'\r\n'.join([
            b'"URL","Title","Image URL","Image crop","Display URL","Brand name","Call to action","Description","Primary impression tracker URL","Secondary impression tracker URL","Label"',  # noqa
            b'"http://testurl.com","Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1","123456789.jpg","center","example.com","Example","Call to action","Example description","http://testurl.com","http://testurl2.com",""',  # noqa
            b'"http://testurl.com","Test Article with no content_ad_sources 1","123456789.jpg","center","example.com","Example","Call to action","Example description","","",""',  # noqa
            b'"http://testurl.com","Test Article with no content_ad_sources 2","123456789.jpg","center","example.com","Example","Call to action","Example description","","",""'  # noqa
        ]) + b'\r\n'

        self.assertEqual(response.content, expected_content)

    def test_get_all_ad_selected(self):
        data = {
            'select_all': True,
            'content_ad_ids_not_selected': '1'
        }

        response = self._get_csv_from_server(data)

        expected_content = b'\r\n'.join([
            b'"URL","Title","Image URL","Image crop","Display URL","Brand name","Call to action","Description","Primary impression tracker URL","Secondary impression tracker URL","Label"',  # noqa
            b'"http://testurl.com","Test Article with no content_ad_sources 1","123456789.jpg","center","example.com","Example","Call to action","Example description","","",""'  # noqa
        ]) + b'\r\n'

        self.assertEqual(response.content, expected_content)

    def test_get_batch(self):
        data = {
            'select_batch': 1,
        }

        response = self._get_csv_from_server(data)

        expected_content = b'\r\n'.join([
            b'"URL","Title","Image URL","Image crop","Display URL","Brand name","Call to action","Description","Primary impression tracker URL","Secondary impression tracker URL","Label"',  # noqa
            b'"http://testurl.com","Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1","123456789.jpg","center","example.com","Example","Call to action","Example description","http://testurl.com","http://testurl2.com",""',  # noqa
            b'"http://testurl.com","Test Article with no content_ad_sources 1","123456789.jpg","center","example.com","Example","Call to action","Example description","","",""',  # noqa
        ]) + b'\r\n'

        self.assertEqual(response.content, expected_content)

    def test_get_batch_ad_selected(self):
        data = {
            'select_batch': 2,
            'content_ad_ids_selected': '6'
        }

        response = self._get_csv_from_server(data, ad_group_id=2)

        expected_content = b'\r\n'.join([
            b'"URL","Title","Image URL","Image crop","Display URL","Brand name","Call to action","Description","Primary impression tracker URL","Secondary impression tracker URL","Label"',
            b'"http://testurl.com","Test Article with no content_ad_sources 3","123456789.jpg","center","example.com","Example","Call to action","Example description","","",""',
            b'"http://testurl.com","Test Article with no content_ad_sources 4","123456789.jpg","center","example.com","Example","Call to action","Example description","","",""',
            b'"http://testurl.com","Test Article with no content_ad_sources 5","123456789.jpg","center","example.com","Example","Call to action","Example description","","",""'
        ]) + b'\r\n'

        self.assertEqual(response.content, expected_content)

    def test_get_ad_selected(self):
        data = {'content_ad_ids_selected': '1,2'}

        response = self._get_csv_from_server(data)

        expected_content = b'\r\n'.join([
            b'"URL","Title","Image URL","Image crop","Display URL","Brand name","Call to action","Description","Primary impression tracker URL","Secondary impression tracker URL","Label"',  # noqa
            b'"http://testurl.com","Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1","123456789.jpg","center","example.com","Example","Call to action","Example description","http://testurl.com","http://testurl2.com",""',  # noqa
            b'"http://testurl.com","Test Article with no content_ad_sources 1","123456789.jpg","center","example.com","Example","Call to action","Example description","","",""',  # noqa
        ]) + b'\r\n'

        self.assertEqual(response.content, expected_content)

    def _get_csv_from_server(self, data, ad_group_id=1):
        return self.client.get(
            reverse(
                'ad_group_content_ad_csv',
                kwargs={'ad_group_id': ad_group_id}),
            data=data,
            follow=True
        )

    def test_get_content_ad_ids_validation_error(self):
        response = self._get_csv_from_server({'content_ad_ids_selected': '1,a'})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')


class CampaignAdGroupStateTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_ad_group_state(self, campaign_id, data):
        return self.client.post(
            reverse(
                'campaign_ad_group_state',
                kwargs={'campaign_id': campaign_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    @patch('automation.autopilot.recalculate_budgets_campaign')
    @patch('dash.dashapi.data_helper.campaign_has_available_budget')
    @patch('dash.views.helpers.validate_ad_groups_state')
    def test_enable(self, mock_validate_state, mock_has_budget, mock_autopilot):
        campaign = models.Campaign.objects.get(pk=1)
        campaign.settings.update_unsafe(None, autopilot=True)
        ad_group_id = 9
        state = constants.AdGroupSettingsState.ACTIVE

        data = {
            'selected_ids': [ad_group_id],
            'state': state,
        }

        response = self._post_ad_group_state(campaign.id, data)
        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        self.assertEqual(ad_group.get_current_settings().state, state)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], [{
            'breakdownId': str(ad_group_id),
            'stats': {
                'state': {
                    'editMessage': None,
                    'isEditable': True,
                    'value': state,
                },
                'status': {'value': state},
            },
        }])
        mock_autopilot.assert_called_once_with(campaign)

    @patch('dash.dashapi.data_helper.campaign_has_available_budget')
    @patch('dash.views.helpers.validate_ad_groups_state')
    def test_pause(self, mock_validate_state, mock_has_budget):
        campaign = models.Campaign.objects.get(pk=1)
        ad_group_id = 9
        state = constants.AdGroupSettingsState.INACTIVE

        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        new_settings = ad_group.get_current_settings().copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE
        new_settings.save(None)

        data = {
            'selected_ids': [ad_group_id],
            'state': state,
        }

        response = self._post_ad_group_state(campaign.id, data)
        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        self.assertEqual(ad_group.get_current_settings().state, state)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], [{
            'breakdownId': str(ad_group_id),
            'stats': {
                'state': {
                    'editMessage': None,
                    'isEditable': True,
                    'value': state,
                },
                'status': {'value': state},
            },
        }])


class CampaignAdGroupArchiveTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_ad_group_archive(self, campaign_id, data):
        return self.client.post(
            reverse(
                'campaign_ad_group_archive',
                kwargs={'campaign_id': campaign_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_post(self):
        campaign = models.Campaign.objects.get(pk=1)
        ad_group_id = 9

        data = {
            'selected_ids': [ad_group_id],
        }

        response = self._post_ad_group_archive(campaign.id, data)
        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        self.assertEqual(ad_group.is_archived(), True)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], [{
            'breakdownId': str(ad_group_id),
            'archived': True,
        }])


class CampaignAdGroupRestoreTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_ad_group_restore(self, campaign_id, data):
        return self.client.post(
            reverse(
                'campaign_ad_group_restore',
                kwargs={'campaign_id': campaign_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_post(self):
        campaign = models.Campaign.objects.get(pk=1)
        ad_group_id = 9

        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        ad_group.archive(None)

        data = {
            'selected_ids': [ad_group_id],
        }

        response = self._post_ad_group_restore(campaign.id, data)
        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        self.assertEqual(ad_group.is_archived(), False)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], [{
            'breakdownId': str(ad_group_id),
            'archived': False,
        }])


class AccountCampaignArchiveTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_campaign_archive(self, account_id, data):
        return self.client.post(
            reverse(
                'account_campaign_archive',
                kwargs={'account_id': account_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_post(self):
        account = models.Account.objects.get(pk=1)
        campaign_id = 2

        data = {
            'selected_ids': [campaign_id],
        }

        response = self._post_campaign_archive(account.id, data)
        campaign = models.Campaign.objects.get(pk=campaign_id)
        self.assertEqual(campaign.is_archived(), True)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], [{
            'breakdownId': str(campaign_id),
            'archived': True,
        }])


class AccountCampaignRestoreTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_campaign_restore(self, account_id, data):
        return self.client.post(
            reverse(
                'account_campaign_restore',
                kwargs={'account_id': account_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_post(self):
        account = models.Account.objects.get(pk=1)
        campaign_id = 2

        campaign = models.Campaign.objects.get(pk=campaign_id)
        campaign.archive(None)

        data = {
            'selected_ids': [campaign_id],
        }

        response = self._post_campaign_restore(account.id, data)
        campaign = models.Campaign.objects.get(pk=campaign_id)
        self.assertEqual(campaign.is_archived(), False)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], [{
            'breakdownId': str(campaign_id),
            'archived': False,
        }])


class AllAccountsAccountArchiveTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_account_archive(self, data):
        return self.client.post(
            reverse(
                'all_accounts_account_archive',
            ),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_post(self):
        account_id = 1

        data = {
            'selected_ids': [account_id],
        }

        response = self._post_account_archive(data)
        account = models.Account.objects.get(pk=account_id)
        self.assertEqual(account.is_archived(), True)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], [{
            'breakdownId': str(account_id),
            'archived': True,
        }])


class AllAccountsAccountRestoreTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_account_restore(self, data):
        return self.client.post(
            reverse(
                'all_accounts_account_restore',
            ),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.client.login(username=self.user.email, password='secret')
        self.factory = RequestFactory()

    def test_post(self):
        account_id = 1

        request = self.factory.get('/')
        request.user = self.user

        account = models.Account.objects.get(pk=account_id)
        account.archive(request)

        data = {
            'selected_ids': [account_id],
        }

        response = self._post_account_restore(data)
        account = models.Account.objects.get(pk=account_id)
        self.assertEqual(account.is_archived(), False)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], [{
            'breakdownId': str(account_id),
            'archived': False,
        }])
