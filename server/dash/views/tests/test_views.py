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


class AdGroupContentAdStateTest(TestCase):
    pass


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
    @patch('dash.views.views.forms.AdGroupAdsPlusUploadForm')
    def test_post(self, MockAdGroupAdsPlusUploadForm, MockProcessUploadThread):
        MockAdGroupAdsPlusUploadForm.return_value.is_valid.return_value = True
        MockProcessUploadThread.return_value.start.return_value = None

        request = HttpRequest()
        request.user = User(id=1)

        ad_group_settings = models.AdGroupSettings(
            ad_group_id=1,
            created_by_id=1,
            brand_name='name',
            display_url='example.com',
            description='test description',
            call_to_action='click here'
        )
        ad_group_settings.save(request)

        mock_file = SimpleUploadedFile('testfile.csv', '')

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}),
            {'content_ads': mock_file},
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

    @patch('dash.views.views.forms.AdGroupAdsPlusUploadForm')
    def test_validation_error_missing_settings(self, MockAdGroupAdsPlusUploadForm):
        MockAdGroupAdsPlusUploadForm.return_value.is_valid.return_value = True
        MockAdGroupAdsPlusUploadForm.return_value.errors = None

        request = HttpRequest()
        request.user = User(id=1)

        ad_group_settings = models.AdGroupSettings(
            ad_group_id=1,
            created_by_id=1,
            brand_name='name',
            description='test description',
        )
        ad_group_settings.save(request)

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}), follow=True)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {
            u'data': {
                u'message': None,
                u'errors': {
                    u'ad_group_settings': u'This ad group needs a Display URL and Call to action before you can add new content ads.'
                },
                u'error_code': u'ValidationError'
            },
            u'success': False
        })

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


class AdGroupSourcesTest(TestCase):
    def test_get_name(self):
        ad_group_source = models.AdGroupSource(
            source=models.Source(
                name="Outbrain",
            ),
            ad_group=models.AdGroup(
                id=123,
                name=u'Ad group š name that is toooooooo long',
                campaign=models.Campaign(
                    name=u'Campaign š name that is toooooooo long',
                    account=models.Account(
                        name=u'Account š name that is toooooooo long',
                    ),
                ),
            ),
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, u'ONE: Account š name that is / Campaign š name that / Ad group š name that / 123 / Outbrain')

    def test_get_name_long_first_word(self):
        ad_group_source = models.AdGroupSource(
            source=models.Source(
                name="Outbrain",
            ),
            ad_group=models.AdGroup(
                id=123,
                name=u'Adgroupšnamethatistoooooooolong',
                campaign=models.Campaign(
                    name=u'Campaignšnamethatistoooooooolong',
                    account=models.Account(
                        name=u'Accountšnamethatistoooooooolong',
                    ),
                ),
            ),
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, u'ONE: Accountšnamethatistooo / Campaignšnamethatistoo / Adgroupšnamethatistooo / 123 / Outbrain')

    def test_get_name_empty_strings(self):
        ad_group_source = models.AdGroupSource(
            source=models.Source(
                name="Outbrain",
            ),
            ad_group=models.AdGroup(
                id=123,
                name=u'',
                campaign=models.Campaign(
                    name=u'',
                    account=models.Account(
                        name=u'',
                    ),
                ),
            ),
        )

        name = ad_group_source.get_external_name()

        self.assertEqual(
            name, u'ONE:  /  /  / 123 / Outbrain')
