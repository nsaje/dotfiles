import json
from mock import patch, ANY

from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from integrations.bizwire import views


@override_settings(BIZWIRE_API_SIGN_KEY='test_api_key')
@patch('integrations.bizwire.config.AUTOMATION_CAMPAIGN', 1)
class PromotionExportTestCase(TestCase):

    fixtures = ['test_bizwire.yaml']

    def setUp(self):
        self.verify_patcher = patch('utils.request_signer.verify_wsgi_request')
        self.mock_verify_wsgi_request = self.verify_patcher.start()

    def tearDown(self):
        self.mock_verify_wsgi_request.assert_called_with(ANY, 'test_api_key')
        self.verify_patcher.stop()

    @patch.object(views.PromotionExport, '_get_ad_stats')
    @patch.object(views.PromotionExport, '_get_geo_stats')
    @patch.object(views.PromotionExport, '_get_pubs_stats')
    def test_get_promotion_export(self, mock_get_pubs_stats, mock_get_geo_stats, mock_get_ad_stats):
        mock_get_ad_stats.return_value = {'impressions': 123, 'clicks': 12, 'ctr': 0.1}
        mock_get_geo_stats.return_value = [{'state': 'US-NY', 'impressions': 100},
                                           {'state': None, 'impressions': 23}]
        mock_get_pubs_stats.return_value = [{'publisher': 'cnn.com'}]

        expected_response = {
            'response': {
                'article': {
                    'description': 'Example description',
                    'title': 'Title 1',
                },
                'statistics': {
                    'headline_impressions': 123,
                    'release_views': 12,
                    'ctr': 0.1,
                    'industry_ctr': 0.17,
                    'geo_headline_impressions': {'US-NY': 100, 'Unknown': 23},
                    'publishers': ['cnn.com'],
                }
            },
            'error': None,
        }

        response = self.client.get(
            reverse('businesswire_promotion_export'),
            {'article_id': 'bizwire_article_1'},
            follow=True,
        )
        self.assertEqual(expected_response, json.loads(response.content))

        response = self.client.get(
            reverse('businesswire_promotion_export'),
            {'article_url': 'http://www.businesswire.com/news/home/bizwire_article_1/en/BizWire_Article_1'},
            follow=True,
        )
        self.assertEqual(expected_response, json.loads(response.content))
