#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from mock import patch
import datetime

from django.test import TestCase, Client, RequestFactory
from django.http.request import HttpRequest
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from zemauth.models import User

from dash import models
from dash import constants
from dash.views import views


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
        self.assertEqual(json.loads(response.content), {'success': True})


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

        expected_content = '''url,title,image_url\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789/200x300.jpg\r
http://testurl.com,Test Article with no content_ad_sources 1,/123456789/200x300.jpg\r
http://testurl.com,Test Article with no content_ad_sources 2,/123456789/200x300.jpg\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_all_ad_disabled(self):
        data = {
            'select_all': True,
            'content_ad_ids_disabled': '1'
        }

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url\r
http://testurl.com,Test Article with no content_ad_sources 1,/123456789/200x300.jpg\r
http://testurl.com,Test Article with no content_ad_sources 2,/123456789/200x300.jpg\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_batch(self):
        data = {
            'select_batch': 1,
        }

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789/200x300.jpg\r
http://testurl.com,Test Article with no content_ad_sources 1,/123456789/200x300.jpg\r
'''

        self.assertEqual(response.content, expected_content)

    def test_get_batch_ad_enabled(self):
        data = {
            'select_batch': 2,
            'content_ad_ids_enabled': '1'
        }

        response = self._get_csv_from_server(data)

        expected_lines = ['url,title,image_url',
                          'http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789/200x300.jpg',
                          'http://testurl.com,Test Article with no content_ad_sources 4,/123456789/200x300.jpg',
                          'http://testurl.com,Test Article with no content_ad_sources 3,/123456789/200x300.jpg',
                          'http://testurl.com,Test Article with no content_ad_sources 2,/123456789/200x300.jpg']

        lines = response.content.split('\r\n')
        self.assertEqual(lines[5], '')

        # disregard the empty line
        lines = lines[:-1]

        self.assertEqual(len(lines), len(expected_lines))
        for line in lines:
            self.assertTrue(line in expected_lines)

    def test_get_ad_enabled(self):
        data = {'content_ad_ids_enabled': '1,2'}

        response = self._get_csv_from_server(data)

        expected_content = '''url,title,image_url\r
http://testurl.com,Test Article unicode \xc4\x8c\xc5\xbe\xc5\xa1,/123456789/200x300.jpg\r
http://testurl.com,Test Article with no content_ad_sources 1,/123456789/200x300.jpg\r
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
        response = self._get_csv_from_server({'content_ad_ids_enabled': '1,a'})
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

    def test_post(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        ad_group_id = 1
        content_ad_id = 1

        data = {
            'state': constants.ContentAdSourceState.INACTIVE,
            'content_ad_ids_enabled': [content_ad_id],
        }

        response = self._post_content_ad_state(ad_group_id, data)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.state, constants.ContentAdSourceState.INACTIVE)

        content_ad_sources = models.ContentAdSource.objects.filter(content_ad=content_ad)
        self.assertEqual(len(content_ad_sources), 2)

        for content_ad_source in content_ad_sources:
            self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.INACTIVE)

        self.assertJSONEqual(response.content, {
            'success': True
        })

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

    @patch('dash.views.views.actionlog.zwei_actions.send_multiple')
    def test_update_content_ads(self, mock_send_multiple):
        content_ad = models.ContentAd.objects.get(pk=1)
        state = constants.ContentAdSourceState.INACTIVE
        request = None

        views.AdGroupContentAdState()._update_content_ads(
            [content_ad], state, request)

        content_ad.refresh_from_db()

        self.assertEqual(content_ad.state, constants.ContentAdSourceState.INACTIVE)

        for content_ad_source in content_ad.contentadsource_set.all():
            self.assertEqual(content_ad_source.state, constants.ContentAdSourceState.INACTIVE)

        self.assertTrue(mock_send_multiple.called)

    def test_get_content_ad_ids_validation_error(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')
        response = self._post_content_ad_state(1, {'content_ad_ids_enabled': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')

    def test_add_to_history(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group).order_by('id')
        self.assertEqual(len(content_ads), 3)

        state = constants.ContentAdSourceState.ACTIVE

        request = HttpRequest()
        request.user = User(id=1)

        views.AdGroupContentAdState()._add_to_history(ad_group, content_ads, state, request)

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

        views.AdGroupContentAdState()._add_to_history(ad_group, content_ads, state, request)

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

    def _login(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_post(self):
        self._login()

        ad_group_id = 1
        content_ad_id = 2

        data = {
            'content_ad_ids_enabled': [content_ad_id],
        }

        response = self._post_content_ad_archive(ad_group_id, data)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.archived, True)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], {'2': {'archived': True}})

    def test_archive_set_all(self):
        self._login()

        ad_group_id = 2
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group_id)

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': True,
        }

        response = self._post_content_ad_archive(ad_group_id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group_id)
        self.assertTrue(all([ad.archived is True for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['data']['rows'], {str(ad.id): {'archived': True} for ad in content_ads})

    def test_archive_set_batch(self):
        self._login()

        ad_group_id = 2
        batch_id = 2
        content_ads = models.ContentAd.objects.filter(batch__id=batch_id)

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': False,
            'select_batch': batch_id,
        }

        response = self._post_content_ad_archive(ad_group_id, payload)

        content_ads = models.ContentAd.objects.filter(batch__id=batch_id)
        self.assertTrue(all([ad.archived is True for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['data']['rows'], {str(ad.id): {'archived': True} for ad in content_ads})

    def test_archive_must_be_paused_validation_error(self):
        self._login()

        ad_group_id = 1
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group_id)
        self.assertGreater(len(content_ads), 0)
        self.assertFalse(all([ad.state == constants.ContentAdSourceState.INACTIVE for ad in content_ads]))

        payload = {
            'select_all': True
        }

        response = self._post_content_ad_archive(ad_group_id, payload)

        content_ads_after = models.ContentAd.objects.filter(ad_group__id=ad_group_id)
        self.assertEqual(len(content_ads), len(content_ads_after))
        self.assertEqual({ad.id: ad.archived for ad in content_ads},
                         {ad.id: ad.archived for ad in content_ads_after})

        response_dict = json.loads(response.content)
        self.assertFalse(response_dict['success'])
        self.assertEqual(response_dict['data']['errors'],
                         'All selected Content Ads must be paused before they can be archived.')

    def test_archive_already_archived_validation_error(self):
        self._login()

        ad_group_id = 2
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group_id)
        for ad in content_ads:
            ad.archived = True
            ad.save()

        self.assertGreater(len(content_ads), 0)
        self.assertTrue(all([ad.state == constants.ContentAdSourceState.INACTIVE
                             for ad in content_ads]))

        payload = {
            'select_all': True
        }

        response = self._post_content_ad_archive(ad_group_id, payload)

        content_ads_after = models.ContentAd.objects.filter(ad_group__id=ad_group_id)
        self.assertEqual(len(content_ads), len(content_ads_after))
        self.assertEqual({ad.id: ad.archived for ad in content_ads},
                         {ad.id: ad.archived for ad in content_ads_after})

        response_dict = json.loads(response.content)
        self.assertFalse(response_dict['success'])
        self.assertEqual(response_dict['data']['errors'], 'These Content Ads have already been archived.')

    def test_content_ad_ids_validation_error(self):
        self._login()
        response = self._post_content_ad_archive(1, {'content_ad_ids_enabled': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')


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

    def _login(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_post(self):
        self._login()

        ad_group_id = 1
        content_ad_id = 2

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        content_ad.archived = True
        content_ad.save()

        data = {
            'content_ad_ids_enabled': [content_ad_id],
        }

        response = self._post_content_ad_restore(ad_group_id, data)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self.assertEqual(content_ad.archived, False)

        response_dict = json.loads(response.content)

        self.assertTrue(response_dict['success'])
        self.assertEqual(response_dict['data']['rows'], {'2': {'archived': False}})

    def test_restore_set_all(self):
        self._login()

        ad_group_id = 2
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group_id)
        for ad in content_ads:
            ad.archived = True
            ad.save()

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': True,
        }

        response = self._post_content_ad_restore(ad_group_id, payload)

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group_id)
        self.assertTrue(all([ad.archived is False for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['data']['rows'], {str(ad.id): {'archived': False} for ad in content_ads})

    def test_archive_set_batch(self):
        self._login()

        ad_group_id = 2
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

        response = self._post_content_ad_restore(ad_group_id, payload)

        content_ads = models.ContentAd.objects.filter(batch__id=batch_id)
        self.assertTrue(all([ad.archived is False for ad in content_ads]))

        response_dict = json.loads(response.content)
        self.assertEqual(response_dict['data']['rows'], {str(ad.id): {'archived': False} for ad in content_ads})

    def test_restore_already_restored_validation_error(self):
        self._login()

        ad_group_id = 2
        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group_id)

        self.assertGreater(len(content_ads), 0)

        payload = {
            'select_all': True
        }

        response = self._post_content_ad_restore(ad_group_id, payload)

        content_ads_after = models.ContentAd.objects.filter(ad_group__id=ad_group_id)
        self.assertEqual(len(content_ads), len(content_ads_after))
        self.assertEqual({ad.id: ad.archived for ad in content_ads},
                         {ad.id: ad.archived for ad in content_ads_after})

        response_dict = json.loads(response.content)
        self.assertFalse(response_dict['success'])
        self.assertEqual(response_dict['data']['errors'], 'These Content Ads are already active.')

    def test_content_ad_ids_validation_error(self):
        self._login()
        response = self._post_content_ad_restore(1, {'content_ad_ids_enabled': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')


class AdGroupContentAdArchiveAllow(TestCase):
    fixtures = ['test_api', 'test_views']

    def _post_content_ad_archive_allow(self, ad_group_id, data):
        return self.client.post(
            reverse(
                'ad_group_content_ad_archive_allow',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def _login(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

    def test_notifications(self):
        self._login()

        ad_group_id = 2

        active = constants.ContentAdSourceState.ACTIVE
        inactive = constants.ContentAdSourceState.INACTIVE

        n1 = {'archive': 'These Content Ads have already been archived.'}
        n2 = {'restore': 'These Content Ads are already active.'}
        n3 = {'archive': 'All selected Content Ads must be paused before they can be archived.'}
        n23 = {'restore': 'These Content Ads are already active.',
               'archive': 'All selected Content Ads must be paused before they can be archived.'}

        cases = [
            # archived, archived, state, expected notifications
            (False, False, inactive, n2),
            (False, False, active, n23),
            (False, True, inactive, {}),
            (False, True, active, n3),
            (True, True, inactive, n1),
            (True, True, active, n1)
        ]

        content_ads = models.ContentAd.objects.filter(ad_group__id=ad_group_id)
        for case in cases:
            ad1 = content_ads[0]
            ad2 = content_ads[1]
            ad1.archived = case[0]
            ad2.archived = case[1]
            ad1.state = ad2.state = case[2]
            ad1.save()
            ad2.save()

            response = self._post_content_ad_archive_allow(ad_group_id, {'select_all': True})

            response_dict = json.loads(response.content)
            if case[3]:
                self.assertEqual(response_dict['data'], case[3])
            self.assertTrue(response_dict['success'])

    def test_content_ad_ids_validation_error(self):
        self._login()
        response = self._post_content_ad_archive_allow(1, {'content_ad_ids_enabled': ['1', 'a']})
        self.assertEqual(json.loads(response.content)['data']['error_code'], 'ValidationError')


class AdGroupAdsPlusUploadTest(TestCase):
    fixtures = ['test_views.yaml']

    def _get_client(self, superuser=True):
        password = 'secret'

        user_id = 1 if superuser else 2
        username = User.objects.get(pk=user_id).email

        client = Client()
        client.login(username=username, password=password)

        return client

    @patch('dash.views.views.threads.ProcessUploadThread')
    def test_post(self, MockProcessUploadThread):
        MockProcessUploadThread.return_value.start.return_value = None

        request = HttpRequest()
        request.user = User(id=1)

        ad_group_settings = models.AdGroupSettings(
            ad_group_id=1,
            created_by_id=1,
        )
        ad_group_settings.save(request)

        mock_file = SimpleUploadedFile('testfile.csv', 'Url,title\nhttp://example.com,testtitle')

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
        self.assertTrue(MockProcessUploadThread.return_value.start.called)

    @patch('dash.views.views.forms.AdGroupAdsPlusUploadForm')
    def test_validation_error(self, MockAdGroupAdsPlusUploadForm):
        MockAdGroupAdsPlusUploadForm.return_value.is_valid.return_value = False
        MockAdGroupAdsPlusUploadForm.return_value.errors = []

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


class AdGroupAdsPlusUploadBatchesTest(TestCase):
    fixtures = ['test_views', 'test_api']

    def setUp(self):
        self.factory = RequestFactory()

    def _get_client(self, superuser=True):
        password = 'secret'
        user_id = 1 if superuser else 2
        username = User.objects.get(pk=user_id).email
        client = Client()
        client.login(username=username, password=password)
        return client

    def test_permission(self):
        response = self._get_client(superuser=False).get(
            reverse('ad_group_ads_plus_upload_batches',
            kwargs={'ad_group_id': 1}),
            follow=True,
        )
        self.assertEqual(response.status_code, 403)

        response = self._get_client(superuser=True).get(
            reverse('ad_group_ads_plus_upload_batches',
            kwargs={'ad_group_id': 1}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_batches(self):
        request = self.factory.get(
            reverse('ad_group_ads_plus_upload_batches', kwargs={'ad_group_id': 1})
        )
        request.user = User.objects.get(pk=1)
        handler = views.AdGroupAdsPlusUploadBatches()
        response = handler.get(request, 1)
        json_blob = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([], json_blob["data"]["batches"])

        # make sure batch has state done now
        uploadBatch = models.UploadBatch.objects.get(pk=1)
        uploadBatch.status = constants.UploadBatchStatus.DONE
        uploadBatch.save()

        response = handler.get(request, 1)
        json_blob = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([{"id": 1, "name": "batch 1"}], json_blob["data"]["batches"])


class AdGroupSourcesTest(TestCase):
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
