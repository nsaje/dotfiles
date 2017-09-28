import json
import math
from mock import patch, ANY, MagicMock
import random

from freezegun import freeze_time

from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.contrib.auth.models import Permission

from integrations.bizwire import config

import dash.constants
import dash.models

from zemauth.models import User


@freeze_time('2016-11-30 12:00:00')
@patch('dash.features.contentupload.upload._invoke_external_validation', MagicMock())
@patch('utils.redirector_helper.insert_adgroup', MagicMock())
@patch('integrations.bizwire.config.AUTOMATION_CAMPAIGN', 1)
@patch('integrations.bizwire.config.AUTOMATION_USER_EMAIL', 'user@test.com')
@patch('integrations.bizwire.config.DAILY_BUDGET_RTB_INITIAL', 0)
@patch('integrations.bizwire.config.DAILY_BUDGET_OB_INITIAL', 0)
@override_settings(LAMBDA_CONTENT_UPLOAD_SIGN_KEY='test_api_key')
class ArticleUploadTest(TestCase):

    fixtures = ['test_bizwire.yaml']

    def setUp(self):
        random.seed(1234)
        self.verify_patcher = patch('utils.request_signer.verify_wsgi_request')
        self.mock_verify_wsgi_request = self.verify_patcher.start()

        permissions = ['can_use_restapi', 'settings_view', 'can_control_ad_group_state_in_table']
        u = User.objects.get(email='user@test.com')
        for permission in permissions:
            u.user_permissions.add(Permission.objects.get(codename=permission))
        u.save()

    def tearDown(self):
        self.mock_verify_wsgi_request.assert_called_with(ANY, 'test_api_key')
        self.verify_patcher.stop()

    def test_article_upload(self):
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

        self.assertEqual(1, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())
        self.assertEqual(
            'Article bizwire_article_2',
            dash.models.UploadBatch.objects.filter(ad_group_id=1).latest('created_dt').name
        )

        ad_group = dash.models.AdGroup.objects.get(id=1)
        ad_group_settings = ad_group.get_current_settings()

        self.assertTrue(ad_group_settings.b1_sources_group_enabled)

        num_existing_ads = 1
        num_ads = num_existing_ads + len(articles_data)

        # NOTE: initial daily budget is patched
        expected_group_daily_budget = math.ceil(num_ads * config.DAILY_BUDGET_PER_ARTICLE * (1 - config.OB_DAILY_BUDGET_PCT))
        self.assertEqual(expected_group_daily_budget, ad_group_settings.b1_sources_group_daily_budget)
        self.assertEqual(dash.constants.AdGroupSourceSettingsState.ACTIVE, ad_group_settings.b1_sources_group_state)

        expected_ob_daily_budget = math.ceil(num_ads * config.DAILY_BUDGET_PER_ARTICLE * config.OB_DAILY_BUDGET_PCT)
        self.assertEqual(
            expected_ob_daily_budget,
            ad_group.adgroupsource_set.get(source__name='Outbrain').get_current_settings().daily_budget_cc
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
        }, {
            'label': 'bizwire_article_4',
            'title': 'Title 4',
            'url': 'http://example.com',
            'image_url': 'http://example.com/image1jpg',
            'image_crop': 'center',
            'description': 'Example description',
            'brand_name': 'Example brand',
            'display_url': 'example.com',
            'call_to_action': 'Read more',
        }, {
            'label': 'bizwire_article_5',
            'title': 'Title 5',
            'url': 'http://example.com',
            'image_url': 'http://example.com/image1jpg',
            'image_crop': 'center',
            'description': 'Example description',
            'brand_name': 'Example brand',
            'display_url': 'example.com',
            'call_to_action': 'Read more',
        }, {
            'label': 'bizwire_article_6',
            'title': 'Title 6',
            'url': 'http://example.com',
            'image_url': 'http://example.com/image1jpg',
            'image_crop': 'center',
            'description': 'Example description',
            'brand_name': 'Example brand',
            'display_url': 'example.com',
            'call_to_action': 'Read more',
        }, {
            'label': 'bizwire_article_7',
            'title': 'Title 7',
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

        self.assertEqual(6, dash.models.ContentAdCandidate.objects.filter(ad_group_id=1).count())
        self.assertEqual(
            'Multiple articles upload',
            dash.models.UploadBatch.objects.filter(ad_group_id=1).latest('created_dt').name
        )

        ad_group = dash.models.AdGroup.objects.get(id=1)
        ad_group_settings = ad_group.get_current_settings()

        self.assertTrue(ad_group_settings.b1_sources_group_enabled)

        num_existing_ads = 1
        num_ads = num_existing_ads + len(articles_data)

        # NOTE: initial daily budget is patched
        expected_group_daily_budget = math.ceil(num_ads * config.DAILY_BUDGET_PER_ARTICLE * (1 - config.OB_DAILY_BUDGET_PCT))
        self.assertEqual(expected_group_daily_budget, ad_group_settings.b1_sources_group_daily_budget)
        self.assertEqual(dash.constants.AdGroupSourceSettingsState.ACTIVE, ad_group_settings.b1_sources_group_state)

        expected_ob_daily_budget = math.ceil(num_ads * config.DAILY_BUDGET_PER_ARTICLE * config.OB_DAILY_BUDGET_PCT)
        self.assertEqual(
            expected_ob_daily_budget,
            ad_group.adgroupsource_set.get(source__name='Outbrain').get_current_settings().daily_budget_cc
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
