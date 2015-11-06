from datetime import date
import json
from mock import patch

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

import reports.views

@patch('reports.api_contentads.query')
@patch('utils.request_signer.verify_wsgi_request')
@override_settings(BIDDER_API_SIGN_KEY='test_api_key')
class CrossvalidationViewTest(TestCase):
    fixtures = ['test_api_views']

    def test_no_parameters(self, mock_verify_wsgi_request, mock_contentads_query):
        response = self.client.get(reverse('api.crossvalidation'))

        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')
        self.assertEqual(response.status_code, 400)

    def test_valid_request(self, mock_verify_wsgi_request, mock_contentads_query):
        mock_contentads_query.return_value = [
            {
                'content_ad': 10,
                'source': 1,
                'ad_group': 1,
                'impressions': None,
                'clicks': None,
                'cost': None,
            },
            {
                'content_ad': 11,
                'source': 1,
                'ad_group': 1,
                'impressions': 10,
                'clicks': 2,
                'cost': 0.033,
            },
            {
                'content_ad': 15,
                'source': 2,
                'ad_group': 2,
                'impressions': 5,
                'clicks': 0,
                'cost': 0.0,
            },
        ]

        response = self.client.get(reverse('api.crossvalidation'), data={'start_date': '2015-11-05', 'end_date': '2015-11-05'})

        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, 'test_api_key')
        mock_contentads_query.assert_called_with(
            date(2015,11,05),
            date(2015,11,05),
            breakdown=['content_ad', 'source', 'ad_group'],
            source__eq=[2,1],
            ad_group__neq=[3],
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'status': 'OK',
            'data': [
                {
                    'content_ad_id': 11,
                    'ad_group_id': 1,
                    'cost': 0.033,
                    'impressions': 10,
                    'clicks': 2,
                    'bidder_slug': 'test1',
                },
                {
                    'content_ad_id': 15,
                    'ad_group_id': 2,
                    'cost': 0.0,
                    'impressions': 5,
                    'clicks': 0,
                    'bidder_slug': 'test2',
                }
            ]
        })
