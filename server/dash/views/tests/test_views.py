#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from mock import patch
import datetime

from django.test import TestCase, Client
from django.http.request import HttpRequest
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from zemauth.models import User

from dash import models
from dash import constants
from dash import api


class UserTest(TestCase):
    fixtures = ['test_views.yaml']

    class MockDatetime(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2015, 3, 1)

    class MockDatetimeNonExistent(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2015, 3, 8, 2, 30)

    class MockDatetimeAmbiguous(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2002, 10, 27, 1, 30, 00)

    @patch('dash.views.views.datetime.datetime', MockDatetime)
    def test_get(self):
        username = User.objects.get(pk=2).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('user', kwargs={'user_id': 'current'}))

        self.assertEqual(json.loads(response.content), {
            'data': {
                'user': {
                    'id': '2',
                    'email': 'user@test.com',
                    'name': '',
                    'permissions': {},
                    'show_onboarding_guidance': False,
                    'timezone_offset': -18000.0
                }
            },
            'success': True
        })

    @patch('dash.views.views.datetime.datetime', MockDatetimeNonExistent)
    def test_get_non_existent_time(self):
        username = User.objects.get(pk=2).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('user', kwargs={'user_id': 'current'}))

        self.assertEqual(json.loads(response.content), {
            'data': {
                'user': {
                    'id': '2',
                    'email': 'user@test.com',
                    'name': '',
                    'permissions': {},
                    'show_onboarding_guidance': False,
                    'timezone_offset': -14400.0
                }
            },
            'success': True
        })

    @patch('dash.views.views.datetime.datetime', MockDatetimeAmbiguous)
    def test_get_ambiguous_time(self):
        self.maxDiff = None
        username = User.objects.get(pk=2).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('user', kwargs={'user_id': 'current'}))

        self.assertEqual(json.loads(response.content), {
            'data': {
                'user': {
                    'id': '2',
                    'email': 'user@test.com',
                    'name': '',
                    'permissions': {},
                    'show_onboarding_guidance': False,
                    'timezone_offset': -14400.0
                }
            },
            'success': True
        })


class AdGroupSourceSettingsTest(TestCase):
    fixtures = ['test_models.yaml', 'test_views.yaml', ]

    class MockSettingsWriter(object):
        def __init__(self, init):
            pass

        def set(self, resource, request):
            pass

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')

    def test_end_date_past(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        settings = ad_group.get_current_settings()
        settings.end_date = datetime.date.today() - datetime.timedelta(days=1)
        settings.save(None)

        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '0.15'})
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

    @patch('dash.views.views.api.AdGroupSourceSettingsWriter', MockSettingsWriter)
    def test_end_date_future(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        settings = ad_group.get_current_settings()
        settings.end_date = datetime.date.today() + datetime.timedelta(days=3)
        settings.save(None)

        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '0.15'})
        )
        self.assertEqual(response.status_code, 200)

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_logs_user_action(self, mock_log_useraction):
        ad_group = models.AdGroup.objects.get(pk=1)
        settings = ad_group.get_current_settings()
        settings.end_date = datetime.date.today()
        settings.save(None)

        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '0.15'})
        )
        self.assertEqual(response.status_code, 200)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_MEDIA_SOURCE_SETTINGS,
            ad_group=ad_group)


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

        expected_content = '''url,title,image_url,description (optional)\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_all_include_archived(self):
        data = {
            'select_all': True,
            'archived': 'true'
        }

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url,description (optional)\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description\r
http://testurl.com,Test Article with no content_ad_sources 2,123456789.jpg,Example description\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_all_ad_selected(self):
        data = {
            'select_all': True,
            'content_ad_ids_not_selected': '1'
        }

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url,description (optional)\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_batch(self):
        data = {
            'select_batch': 1,
        }

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url,description (optional)\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_batch_ad_selected(self):
        data = {
            'select_batch': 2,
            'content_ad_ids_selected': '1'
        }

        response = self._get_csv_from_server(data)

        expected_lines = ['url,title,image_url,description (optional)',
                          'http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description',
                          'http://testurl.com,Test Article with no content_ad_sources 4,123456789.jpg,Example description',
                          'http://testurl.com,Test Article with no content_ad_sources 3,123456789.jpg,Example description']

        lines = response.content.splitlines()

        self.assertEqual(len(lines), len(expected_lines))
        self.assertItemsEqual(lines, expected_lines)

    def test_get_ad_selected(self):
        data = {'content_ad_ids_selected': '1,2'}

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url,description (optional)\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,123456789.jpg,Example description\r
http://testurl.com,Test Article with no content_ad_sources 1,123456789.jpg,Example description\r
'''

        self.assertEqual(response.content, expected_content)

    def _get_csv_from_server(self, data):
        return self.client.get(
            reverse(
                'ad_group_content_ad_csv',
                kwargs={'ad_group_id': 1}),
            data=data,
            follow=True
        )

    def test_get_content_ad_ids_validation_error(self):
        response = self._get_csv_from_server({'content_ad_ids_selected': '1,a'})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')


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

    @patch('dash.views.helpers.log_useraction_if_necessary')
    def test_post(self, mock_log_useraction):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        ad_group_id = 1
        content_ad_id = 1

        data = {
            'state': constants.ContentAdSourceState.INACTIVE,
            'content_ad_ids_selected': [content_ad_id],
        }

        response = self._post_content_ad_state(ad_group_id, data)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.state, constants.ContentAdSourceState.INACTIVE)

        content_ad_sources = models.ContentAdSource.objects.filter(content_ad=content_ad)
        self.assertEqual(len(content_ad_sources), 3)

        for content_ad_source in content_ad_sources:
            self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.INACTIVE)

        self.assertJSONEqual(response.content, {
            'success': True
        })

        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.SET_CONTENT_AD_STATE,
            ad_group=models.AdGroup.objects.get(pk=1))

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
            'content_ad_ids_selected': [archived_ad.id, restored_ad.id],
            'state': constants.ContentAdSourceState.ACTIVE,
        }

        self._post_content_ad_state(2, payload)

        archived_ad.refresh_from_db()
        self.assertEqual(archived_ad.state, constants.ContentAdSourceState.INACTIVE)

        restored_ad.refresh_from_db()
        self.assertEqual(restored_ad.state, constants.ContentAdSourceState.ACTIVE)

    @patch('dash.views.views.actionlog.zwei_actions.send')
    def test_update_content_ads(self, mock_send):
        content_ad = models.ContentAd.objects.get(pk=1)
        state = constants.ContentAdSourceState.INACTIVE
        request = None

        api.update_content_ads_state([content_ad], state, request)

        content_ad.refresh_from_db()

        self.assertEqual(content_ad.state, constants.ContentAdSourceState.INACTIVE)

        for content_ad_source in content_ad.contentadsource_set.all():
            self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.INACTIVE)

        self.assertTrue(mock_send.called)

    def test_get_content_ad_ids_validation_error(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')
        response = self._post_content_ad_state(1, {'content_ad_ids_selected': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        state = constants.ContentAdSourceState.ACTIVE

        request = HttpRequest()
        request.user = User(id=1)

        api.add_content_ads_state_change_to_history(ad_group, content_ads, state, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(settings.changes_text, 'Content ad(s) 1, 2, 3 set to Enabled.')

    def test_add_to_history_shorten(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)
        content_ads = list(content_ads) * 4  # need more than 10 ads

        state = constants.ContentAdSourceState.ACTIVE

        request = HttpRequest()
        request.user = User(id=1)

        api.add_content_ads_state_change_to_history(ad_group, content_ads, state, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(
            settings.changes_text,
            'Content ad(s) 1, 2, 3, 1, 2, 3, 1, 2, 3, 1 and 2 more set to Enabled.'
        )


class AdGroupContentAdArchive(TestCase):
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

    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_post(self, mock_send_mail, mock_log_useraction):
        ad_group = models.AdGroup.objects.get(pk=1)
        content_ad_id = 2

        data = {
            'content_ad_ids_selected': [content_ad_id],
        }

        response = self._post_content_ad_archive(ad_group.id, data)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.archived, True)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], {
            '2': {
                'archived': True,
                'status_setting': 2
            }})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.ARCHIVE_RESTORE_CONTENT_AD,
            ad_group=ad_group
        )

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
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
        self.assertEqual(response_dict['data']['rows'],
                         {str(ad.id): {
                             'archived': True,
                             'status_setting': ad.state
                         } for ad in content_ads})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
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
        self.assertEqual(response_dict['data']['rows'],
                         {str(ad.id): {
                             'archived': True,
                             'status_setting': ad.state
                         } for ad in content_ads})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
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
        self.assertEqual(response_dict['data']['active_count'], active_count)
        self.assertEqual(response_dict['data']['archived_count'], archived_count)

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_content_ad_ids_validation_error(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)

        response = self._post_content_ad_archive(ad_group.id, {'content_ad_ids_selected': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

        self.assertFalse(mock_send_mail.called)

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        request = HttpRequest()
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history(ad_group, content_ads, True, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(settings.changes_text, 'Content ad(s) 1, 2, 3 Archived.')

    def test_add_to_history_shorten(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)
        content_ads = list(content_ads) * 4  # need more than 10 ads

        request = HttpRequest()
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history(ad_group, content_ads, True, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(
            settings.changes_text,
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

    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_post(self, mock_send_mail, mock_log_useraction):
        ad_group = models.AdGroup.objects.get(pk=1)
        content_ad_id = 2

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        content_ad.archived = True
        content_ad.save()

        data = {
            'content_ad_ids_selected': [content_ad_id],
        }

        response = self._post_content_ad_restore(ad_group.id, data)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.archived, False)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], {'2': {'archived': False, 'status_setting': content_ad.state}})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.ARCHIVE_RESTORE_CONTENT_AD,
            ad_group=ad_group
        )

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
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
        self.assertEqual(response_dict['data']['rows'],
                         {str(ad.id): {
                             'archived': False,
                             'status_setting': ad.state
                         } for ad in content_ads})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
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
        self.assertEqual(response_dict['data']['rows'],
                         {str(ad.id): {
                             'archived': False,
                             'status_setting': ad.state
                         } for ad in content_ads})

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
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

        mock_send_mail.assert_called_with(ad_group, response.wsgi_request)

    @patch('dash.views.views.email_helper.send_ad_group_notification_email')
    def test_content_ad_ids_validation_error(self, mock_send_mail):
        ad_group = models.AdGroup.objects.get(pk=1)

        response = self._post_content_ad_restore(ad_group.id, {'content_ad_ids_selected': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

        self.assertFalse(mock_send_mail.called)

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        request = HttpRequest()
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history(ad_group, content_ads, False, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(settings.changes_text, 'Content ad(s) 1, 2, 3 Restored.')

    def test_add_to_history_shorten(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)
        content_ads = list(content_ads) * 4  # need more than 10 ads

        request = HttpRequest()
        request.user = User(id=1)

        api.add_content_ads_archived_change_to_history(ad_group, content_ads, False, request)

        settings = ad_group.get_current_settings()

        self.assertEqual(
            settings.changes_text,
            'Content ad(s) 1, 2, 3, 1, 2, 3, 1, 2, 3, 1 and 2 more Restored.'
        )


class AdGroupAdsPlusUploadTest(TestCase):
    fixtures = ['test_views.yaml']

    def _get_client(self, superuser=True):
        password = 'secret'

        user_id = 1 if superuser else 2
        username = User.objects.get(pk=user_id).email

        client = Client()
        client.login(username=username, password=password)

        return client

    @patch('dash.views.helpers.log_useraction_if_necessary')
    @patch('dash.views.views.upload.process_async')
    def test_post(self, mock_process_async, mock_log_useraction):
        request = HttpRequest()
        request.user = User(id=1)

        ad_group_settings = models.AdGroupSettings(
            ad_group_id=1,
            created_by_id=1,
        )
        ad_group_settings.save(request)

        mock_file = SimpleUploadedFile('testfile.csv', 'Url,title,image_url\nhttp://example.com,testtitle,http://example.com/image')

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}),
            {
                'content_ads': mock_file,
                'batch_name': 'testname',
                'display_url': 'test.com',
                'brand_name': 'testbrand',
                'description': 'testdesc',
                'call_to_action': 'testcall',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_process_async.called)
        mock_log_useraction.assert_called_with(
            response.wsgi_request,
            constants.UserActionType.UPLOAD_CONTENT_ADS,
            ad_group=models.AdGroup.objects.get(pk=1))

    @patch('dash.views.views.upload.process_async')
    def test_post_empty_fields_not_in_csv(self, mock_process_async):
        request = HttpRequest()
        request.user = User(id=1)

        ad_group_settings = models.AdGroupSettings(
            ad_group_id=1,
            created_by_id=1,
        )
        ad_group_settings.save(request)

        mock_file = SimpleUploadedFile('testfile.csv', 'Url,title,image_url\nhttp://example.com,testtitle,http://example.com/image')

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}),
            {
                'content_ads': mock_file,
                'batch_name': 'testname',
                'display_url': '',
                'brand_name': '',
                'description': '',
                'call_to_action': '',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content),
                    {
                        "data": {
                        "message": None,
                        "errors": {
                            "display_url": ["This field is required."],
                            "call_to_action": ["This field is required."],
                            "brand_name": ["This field is required."],
                            "description": ["This field is required."],
                            },
                        "error_code": "ValidationError"
                        },
                        "success": False
                    })
        self.assertFalse(mock_process_async.called)

    def test_validation_error(self):
        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}), follow=True)

        self.assertEqual(response.status_code, 400)

    def test_permission(self):
        response = self._get_client(superuser=False).post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}), follow=True)

        self.assertEqual(response.status_code, 403)

    def test_missing_ad_group(self):
        non_existent_ad_group_id = 0

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': non_existent_ad_group_id}),
            follow=True
        )

        self.assertEqual(response.status_code, 404)

    def test_description_too_long(self):
        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}),
            {
                'description': 'a'*141
            },
            follow=True
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Description is too long', response.content)

    def test_description_right_length(self):
        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}),
            {
                'description': 'a'*140
            },
            follow=True
        )

        self.assertNotIn('Description is too long', response.content)


class AdGroupAdsPlusUploadStatusTest(TestCase):

    fixtures = ['test_views.yaml']

    def _get_client(self, superuser=True):
        password = 'secret'

        user_id = 1 if superuser else 2
        username = User.objects.get(pk=user_id).email

        client = Client()
        client.login(username=username, password=password)

        return client

    def _get_status(self):
        response = self._get_client().get(
            reverse('ad_group_ads_plus_upload_status', kwargs={'ad_group_id': 1, 'batch_id': 2}), follow=True)

        return json.loads(response.content)['data']

    def test_get(self):
        batch = models.UploadBatch.objects.get(pk=2)
        batch.processed_content_ads = 55
        batch.save()

        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.IN_PROGRESS,
            'step': 'Processing imported file (step 1/3)',
            'count': 55,
            'all': 100
        })

        batch.inserted_content_ads = 55
        batch.save()

        # processing ended
        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.IN_PROGRESS,
            'step': 'Inserting content ads (step 2/3)',
            'count': 55,
            'all': 100
        })

        # inserting ended
        batch.inserted_content_ads = batch.batch_size
        batch.save()

        response = self._get_status()
        self.assertEqual(response, {
            'status': constants.UploadBatchStatus.IN_PROGRESS,
            'step': 'Sending to external sources (step 3/3)',
            'count': 0,
            'all': 0
        })

    def test_permission(self):
        response = self._get_client(superuser=False).get(
            reverse('ad_group_ads_plus_upload_status', kwargs={'ad_group_id': 1, 'batch_id': 2}), follow=True)

        self.assertEqual(response.status_code, 403)


class AdGroupSourcesTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def test_get_name(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = models.Account(
            name=u'Account š name that is toooooooo long',
        )
        account.save(request)

        campaign = models.Campaign(
            name=u'Campaign š name that is toooooooo long',
            account=account,
        )
        campaign.save(request)

        source = models.Source(
            name="Outbrain",
        )
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(
                id=123,
                name=u'Ad group š name that is toooooooo long',
                campaign=campaign,
            ),
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, u'ONE: Account š name that is / Campaign š name that / Ad group š name that / 123 / Outbrain')

    def test_get_name_long_first_word(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = models.Account(
            name=u'Accountšnamethatistoooooooolong',
        )
        account.save(request)

        campaign = models.Campaign(
            name=u'Campaignšnamethatistoooooooolong',
            account=account,
        )
        campaign.save(request)

        source = models.Source(
            name="Outbrain",
        )
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(
                id=123,
                name=u'Adgroupšnamethatistoooooooolong',
                campaign=campaign,
            ),
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, u'ONE: Accountšnamethatistooo / Campaignšnamethatistoo / Adgroupšnamethatistooo / 123 / Outbrain')

    def test_get_name_empty_strings(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = models.Account(
            name=u'',
        )
        account.save(request)

        campaign = models.Campaign(
            name=u'',
            account=account,
        )
        campaign.save(request)

        source = models.Source(
            name="Outbrain",
        )
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(
                id=123,
                name=u'',
                campaign=campaign,
            ),
        )

        name = ad_group_source.get_external_name()

        self.assertEqual(
            name, u'ONE:  /  /  / 123 / Outbrain')

    def test_get_dma_targeting_compatible(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        ad_group_source = models.AdGroupSource.objects.get(id=3)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.CAN_MODIFY_DMA_TARGETING_AUTOMATIC,
        ]
        ad_group_source.source.source_type.save()

        response = self.client.get(
            reverse(
                'ad_group_sources',
                kwargs={'ad_group_id': 2}),
            follow=True
        )

        response_dict = json.loads(response.content)
        self.assertItemsEqual(response_dict['data']['sources'], [
            {'id': 2, 'name': 'Gravity', 'can_target_existing_regions': False},  # should return False when DMAs used
            {'id': 3, 'name': 'Outbrain', 'can_target_existing_regions': True},
        ])


@patch('dash.views.views.actionlog.api_contentads.init_update_content_ad_action')
class SharethroughApprovalTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.client = Client()

    def test_approved_creative(self, mock_update):
        data = {
            'status': 0,
            'crid': 1,
            'seat': 'abc123',
            'expiry': '2015-12-31'
        }
        cas = models.ContentAdSource.objects.get(content_ad_id=1, source=models.Source.objects.get(name='Sharethrough'))
        self.assertEqual(1, cas.submission_status)

        self.client.post(
            reverse('sharethrough_approval'),
            follow=True,
            content_type='application/json',
            data=json.dumps(data)
        )

        cas = models.ContentAdSource.objects.get(id=cas.id)

        self.assertEqual(2, cas.submission_status)
        self.assertEqual(None, cas.submission_errors)
        self.assertTrue(mock_update.called)
        mock_update.assert_called_with(cas, {'state': cas.state}, request=None, send=True)

    def test_rejected_creative(self, mock_update):
        data = {
            'status': 1,
            'crid': 1,
            'seat': 'abc123',
            'expiry': '2015-12-31'
        }
        cas = models.ContentAdSource.objects.get(content_ad_id=1, source=models.Source.objects.get(name='Sharethrough'))
        self.assertEqual(1, cas.submission_status)

        self.client.post(
            reverse('sharethrough_approval'),
            follow=True,
            content_type='application/json',
            data=json.dumps(data)
        )

        cas = models.ContentAdSource.objects.get(id=cas.id)

        self.assertEqual(3, cas.submission_status)
        self.assertEqual(None, cas.submission_errors)
        self.assertTrue(mock_update.called)
        mock_update.assert_called_with(cas, {'state': cas.state}, request=None, send=True)
