import time

from mock import patch, ANY

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

import dash.features.geolocation
import dash.features.ga
import dash.constants
import dash.models

import logging

from utils import request_signer


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class K1APIBaseTest(TestCase):

    fixtures = ['test_publishers.yaml', 'test_k1_api.yaml']

    def setUp(self):
        self.test_signature = True
        settings.K1_API_SIGN_KEY = ['test_api_key']
        settings.BIDDER_API_SIGN_KEY = ['test_api_key2']
        self.verify_patcher = patch('utils.request_signer.verify_wsgi_request')
        self.mock_verify_wsgi_request = self.verify_patcher.start()
        self.campaign = dash.models.Campaign.objects.all().first()

        self.maxDiff = None

    def tearDown(self):
        if self.test_signature:
            self.mock_verify_wsgi_request.assert_called_with(ANY, ['test_api_key', 'test_api_key2'])
        self.verify_patcher.stop()

    def assert_response_ok(self, response, data):
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', data)
        self.assertEqual(data['error'], None)
        self.assertIn('response', data)
        self.assertNotEqual(data['response'], None)


class K1APITest(K1APIBaseTest):
    def test_404_without_signature(self):
        self.test_signature = False
        self.mock_verify_wsgi_request.side_effect = request_signer.SignatureError
        test_paths = [
            'k1api.ad_groups',
            'k1api.ad_groups.sources',
            'k1api.content_ads',
            'k1api.content_ads.sources',
            'k1api.accounts',
            'k1api.sources',
            'k1api.source_pixels',
            'k1api.ga_accounts',
            'k1api.publisher_groups',
        ]
        for path in test_paths:
            self._test_signature(path)

    def _test_signature(self, path):
        response = self.client.get(
            reverse(path),
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.get(
            reverse(path),
            TS_HEADER=str(int(time.time())),
            SIGNATURE_HEADER='abc'
        )
        self.assertEqual(response.status_code, 404)
