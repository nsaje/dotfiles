from mock import patch

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from zemauth.models import User

from dash.views import views
from dash import models


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
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(MockProcessUploadThread.return_value.start.called)

    @patch('dash.views.views.forms.AdGroupAdsPlusUploadForm')
    def test_validation_error(self, MockAdGroupAdsPlusUploadForm):
        MockAdGroupAdsPlusUploadForm.return_value.is_valid.return_value = False
        MockAdGroupAdsPlusUploadForm.return_value.errors = []

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}))

        self.assertEqual(response.status_code, 400)

    def test_permission(self):
        response = self._get_client(superuser=False).post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': 1}))

        self.assertEqual(response.status_code, 403)

    def test_missing_ad_group(self):
        non_existent_ad_group_id = 0

        response = self._get_client().post(
            reverse('ad_group_ads_plus_upload', kwargs={'ad_group_id': non_existent_ad_group_id}))

        self.assertEqual(response.status_code, 404)


class ProcessUploadThreadTest(TestCase):
    @patch('dash.views.views.image.process_image')
    def test_run(self, mock_process_image):
        image_id = 'test_image_id'
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

        mock_process_image.return_value = image_id

        thread = views.ProcessUploadThread(content_ads, batch_name, ad_group_id)
        thread.run()

        mock_process_image.assert_called_with(image_url, crop_areas)

        article = models.Article.objects.latest()
        self.assertEqual(article.title, title)
        self.assertEqual(article.url, url)
        self.assertEqual(article.ad_group_id, ad_group_id)

        self.assertEqual(article.content_ad.image_id, image_id)
        self.assertEqual(article.content_ad.batch.name, batch_name)
