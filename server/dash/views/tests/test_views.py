import json
from mock import patch
import datetime

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from zemauth.models import User

from dash.views import views
from dash import models
from dash import image_helper
from dash import constants

import actionlog.models


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


class AdGroupAdsPlusUploadTest(TestCase):
    fixtures = ['test_views.yaml']

    def _get_client(self, superuser=True):
        password = 'secret'

        user_id = 1 if superuser else 2
        username = User.objects.get(pk=user_id).email

        client = Client()
        client.login(username=username, password=password)

        return client

    @patch('dash.views.views.ProcessUploadThread')
    @patch('dash.views.views.forms.AdGroupAdsPlusUploadForm')
    def test_post(self, MockAdGroupAdsPlusUploadForm, MockProcessUploadThread):
        MockAdGroupAdsPlusUploadForm.return_value.is_valid.return_value = True
        MockProcessUploadThread.return_value.start.return_value = None

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}), follow=True)

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


class ProcessUploadThreadTest(TestCase):
    @patch('dash.views.views.image_helper.process_image')
    def test_run(self, mock_process_image):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]

        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }]
        batch_name = 'Test batch name'
        ad_group_id = 1

        batch = models.UploadBatch.objects.create(name=batch_name)

        mock_process_image.return_value = image_id, image_width, image_height

        thread = views.ProcessUploadThread(content_ads, batch, ad_group_id, None)
        prev_actionlog_count = actionlog.models.ActionLog.objects.all().count()
        thread.run()

        mock_process_image.assert_called_with(image_url, crop_areas)

        article = models.Article.objects.latest()
        self.assertEqual(article.title, title)
        self.assertEqual(article.url, url)
        self.assertEqual(article.ad_group_id, ad_group_id)

        self.assertEqual(article.content_ad.image_id, image_id)
        self.assertEqual(article.content_ad.image_width, image_width)
        self.assertEqual(article.content_ad.image_height, image_height)
        self.assertEqual(article.content_ad.batch.name, batch_name)

        self.assertEqual(prev_actionlog_count, actionlog.models.ActionLog.objects.all().count())
        self.assertEqual(batch.status, constants.UploadBatchStatus.DONE)

    @patch('dash.views.views.image_helper.process_image')
    @patch('dash.views.views.actionlog.api_contentads.init_insert_content_ad_action')
    def test_image_processing_exception(self, mock_insert_action, mock_process_image):
        image_id = 'test_image_id'
        image_width = 100
        image_height = 200

        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]

        # two content ads
        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }, {
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }]
        batch_name = 'Test batch name'
        ad_group_id = 1

        batch = models.UploadBatch.objects.create(name=batch_name)

        # raise ImageProcessingException for the second ad
        mock_process_image.side_effect = [
            (image_id, image_width, image_height),
            image_helper.ImageProcessingException
        ]

        thread = views.ProcessUploadThread(content_ads, batch, ad_group_id, None)
        thread.run()

        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)
        self.assertFalse(mock_insert_action.called)

    @patch('dash.views.views.image_helper.process_image')
    @patch('dash.views.views.actionlog.api_contentads.init_insert_content_ad_action')
    def test_exception(self, mock_insert_action, mock_process_image):
        url = 'http://example.com'
        title = 'test title'
        image_url = 'http://example.com/image'
        crop_areas = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]

        # two content ads
        content_ads = [{
            'url': url,
            'title': title,
            'image_url': image_url,
            'crop_areas': crop_areas
        }]
        batch_name = 'Test batch name'
        ad_group_id = 1

        batch = models.UploadBatch.objects.create(name=batch_name)

        # raise ImageProcessingException for the second ad
        mock_process_image.side_effect = Exception

        thread = views.ProcessUploadThread(content_ads, batch, ad_group_id, None)

        with self.assertRaises(Exception):
            thread.run()

        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)
        self.assertFalse(mock_insert_action.called)
