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

from utils import exc


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


class AdGroupContentAdStateTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        self.factory = RequestFactory()

    def test_post(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        ad_group_id = 1
        content_ad_id = 1

        data = {
            'state': constants.ContentAdSourceState.INACTIVE,
            'content_ad_ids_enabled': [content_ad_id],
        }

        response = self.client.post(
            reverse(
                'ad_group_content_ad_state',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

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

        self.client.post(
            reverse(
                'ad_group_content_ad_state',
                kwargs={'ad_group_id': 1}),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

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

        self.client.post(
            reverse(
                'ad_group_content_ad_state',
                kwargs={'ad_group_id': 1}),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

        content_ads = models.ContentAd.objects.filter(batch__id=1)
        self.assertTrue(all([ad.state == constants.ContentAdSourceState.INACTIVE
                             for ad in content_ads]))

    def test_get_content_ads_all(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_enabled = []
        content_ad_ids_disabled = []

        content_ads = views.AdGroupContentAdState()._get_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_enabled, content_ad_ids_disabled)

        self._assert_content_ads(content_ads, [1, 2, 3])

    def test_get_content_ads_all_disabled(self):
        ad_group_id = 1
        select_all = True
        select_batch_id = None
        content_ad_ids_enabled = []
        content_ad_ids_disabled = [1]

        content_ads = views.AdGroupContentAdState()._get_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_enabled, content_ad_ids_disabled)

        self._assert_content_ads(content_ads, [2, 3])

    def test_get_content_ads_batch(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_enabled = []
        content_ad_ids_disabled = []

        content_ads = views.AdGroupContentAdState()._get_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_enabled, content_ad_ids_disabled)

        self._assert_content_ads(content_ads, [1, 2])

    def test_get_content_ads_batch_enabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_enabled = [3]
        content_ad_ids_disabled = []

        content_ads = views.AdGroupContentAdState()._get_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_enabled, content_ad_ids_disabled)

        self._assert_content_ads(content_ads, [1, 2, 3])

    def test_get_content_ads_batch_disabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = 1
        content_ad_ids_enabled = []
        content_ad_ids_disabled = [1]

        content_ads = views.AdGroupContentAdState()._get_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_enabled, content_ad_ids_disabled)

        self._assert_content_ads(content_ads, [2])

    def test_get_content_ads_only_enabled(self):
        ad_group_id = 1
        select_all = False
        select_batch_id = None
        content_ad_ids_enabled = [1, 3]
        content_ad_ids_disabled = []

        content_ads = views.AdGroupContentAdState()._get_content_ads(
            ad_group_id, select_all, select_batch_id, content_ad_ids_enabled, content_ad_ids_disabled)

        self._assert_content_ads(content_ads, [1, 3])

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

    def test_get_content_ad_ids(self):
        data = {'ids': ['1', '2']}
        param_name = 'ids'

        result = views.AdGroupContentAdState()._get_content_ad_ids(data, param_name)

        self.assertEqual(result, [1, 2])

    def test_get_content_ad_ids_validation_error(self):
        data = {'ids': ['1', 'a']}
        param_name = 'ids'

        with self.assertRaises(exc.ValidationError):
            views.AdGroupContentAdState()._get_content_ad_ids(data, param_name)

    def _assert_content_ads(self, content_ads, expected_ids):
        self.assertQuerysetEqual(
            content_ads, expected_ids, transform=lambda ad: ad.id, ordered=False)


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
