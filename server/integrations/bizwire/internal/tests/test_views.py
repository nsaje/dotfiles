import json
from mock import patch, ANY, MagicMock

from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

import dash.constants
import dash.models


@patch('dash.upload._invoke_external_validation', MagicMock())
@patch('integrations.bizwire.config.AUTOMATION_CAMPAIGN', 1)
@patch('integrations.bizwire.config.TEST_FEED_AD_GROUP', 2)
@override_settings(LAMBDA_CONTENT_UPLOAD_SIGN_KEY='test_api_key')
class ArticleUploadTest(TestCase):

    fixtures = ['test_bizwire.yaml']

    def setUp(self):
        self.verify_patcher = patch('utils.request_signer.verify_wsgi_request')
        self.mock_verify_wsgi_request = self.verify_patcher.start()

    def tearDown(self):
        self.mock_verify_wsgi_request.assert_called_with(ANY, 'test_api_key')
        self.verify_patcher.stop()

    def test_article_upload(self):
        self.assertEqual(0, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())
        article_data = {
            'label': 'bizwire_article_2',
            'title': 'Title 2',
            'url': 'http://example.com',
            'image_url': 'http://example.com/image.jpg',
            'image_crop': 'center',
            'description': 'Example description',
            'brand_name': 'Example brand',
            'display_url': 'example.com',
            'call_to_action': 'Read more',
        }
        response = self.client.post(
            reverse('businesswire_article_upload'),
            data=json.dumps([article_data]),
            content_type='application/json',
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'status': 'ok',
        }, json.loads(response.content))

        self.assertEqual(1, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())
        self.assertEqual(
            'Article bizwire_article_2',
            dash.models.UploadBatch.objects.filter(ad_group_id=1).latest('created_dt').name
        )

    def test_duplicate(self):
        self.assertEqual(0, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())
        article_data = {
            'label': 'bizwire_article_1',
            'title': 'Title 2',
            'url': 'http://example.com',
            'image_url': 'http://example.com/image.jpg',
            'image_crop': 'center',
            'description': 'Example description',
            'brand_name': 'Example brand',
            'display_url': 'example.com',
            'call_to_action': 'Read more',
        }
        response = self.client.post(
            reverse('businesswire_article_upload'),
            data=json.dumps([article_data]),
            content_type='application/json',
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'status': 'ok',
        }, json.loads(response.content))
        self.assertEqual(0, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())

    def test_multiple(self):
        self.assertEqual(0, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())
        articles_data = [{
            'label': 'bizwire_article_2',
            'title': 'Title 2',
            'url': 'http://example.com',
            'image_url': 'http://example.com/image.jpg',
            'image_crop': 'center',
            'description': 'Example description',
            'brand_name': 'Example brand',
            'display_url': 'example.com',
            'call_to_action': 'Read more',
        }, {
            'label': 'bizwire_article_3',
            'title': 'Title 3',
            'url': 'http://example.com',
            'image_url': 'http://example.com/image1jpg',
            'image_crop': 'center',
            'description': 'Example description',
            'brand_name': 'Example brand',
            'display_url': 'example.com',
            'call_to_action': 'Read more',
        }]
        response = self.client.post(
            reverse('businesswire_article_upload'),
            data=json.dumps(articles_data),
            content_type='application/json',
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'status': 'ok',
        }, json.loads(response.content))

        self.assertEqual(2, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())
        self.assertEqual(
            'Multiple articles upload',
            dash.models.UploadBatch.objects.filter(ad_group_id=1).latest('created_dt').name
        )

    def test_article_from_test_feed(self):
        self.assertEqual(0, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())
        self.assertEqual(0, dash.models.ContentAdCandidate.objects.filter(ad_group_id=2).count())
        article_data = {
            'label': 'bizwire_article_2',
            'title': 'Title 2',
            'url': 'http://example.com',
            'image_url': 'http://example.com/image.jpg',
            'image_crop': 'center',
            'description': 'Example description',
            'brand_name': 'Example brand',
            'display_url': 'example.com',
            'call_to_action': 'Read more',
            'meta': {
                'is_test_feed': True,
            }
        }
        response = self.client.post(
            reverse('businesswire_article_upload'),
            data=json.dumps([article_data]),
            content_type='application/json',
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual({
            'status': 'ok',
        }, json.loads(response.content))

        self.assertEqual(0, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())
        self.assertEqual(1, dash.models.ContentAdCandidate.objects.filter(ad_group_id=2).count())

        self.assertEqual(
            'Article bizwire_article_2',
            dash.models.UploadBatch.objects.filter(ad_group_id=2).latest('created_dt').name
        )


@patch('integrations.bizwire.config.AUTOMATION_CAMPAIGN', 1)
@override_settings(R1_API_SIGN_KEY='test_api_key')
class ClickCappingTest(TestCase):

    fixtures = ['test_bizwire.yaml']

    def setUp(self):
        self.verify_patcher = patch('utils.request_signer.verify_wsgi_request')
        self.mock_verify_wsgi_request = self.verify_patcher.start()

    def tearDown(self):
        self.mock_verify_wsgi_request.assert_called_with(ANY, 'test_api_key')
        self.verify_patcher.stop()

    def test_click_capping(self):
        content_ad = dash.models.ContentAd.objects.get(id=1)
        self.assertEqual(dash.constants.ContentAdSourceState.ACTIVE, content_ad.state)
        response = self.client.get(
            reverse('businesswire_click_capping'),
            {'creativeId': 1},
        )
        self.assertEqual(200, response.status_code)

        content_ad.refresh_from_db()
        self.assertEqual(dash.constants.ContentAdSourceState.INACTIVE, content_ad.state)
