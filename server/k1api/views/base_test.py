import time
from itertools import cycle
from mock import patch, ANY, Mock

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

import dash.features.geolocation
import dash.features.ga
import dash.constants
import dash.models

import logging

from .. import urls


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class K1APIBaseTest(TestCase):

    fixtures = ['test_publishers.yaml', 'test_k1_api.yaml']

    def setUp(self):
        self.test_signature = True
        self.verify_patcher = patch('utils.request_signer.verify_wsgi_request')
        self.mock_verify_wsgi_request = self.verify_patcher.start()
        self.mock_verify_wsgi_request.side_effect = cycle([Exception, Exception])

        oauth_result = Mock()
        oauth_result.user.email = 'sspd@service.zemanta.com'
        self.oauth_patcher = patch('utils.rest_common.authentication.get_oauthlib_core')
        self.mock_verify_oauth = self.oauth_patcher.start()
        self.mock_verify_oauth.return_value.verify_request.return_value = (True, oauth_result)

        self.campaign = dash.models.Campaign.objects.all().first()

        self.maxDiff = None

    def tearDown(self):
        if self.test_signature:
            self.mock_verify_wsgi_request.assert_any_call(ANY, settings.K1_API_SIGN_KEY)
            self.mock_verify_wsgi_request.assert_any_call(ANY, settings.BIDDER_API_SIGN_KEY)
            self.mock_verify_oauth.return_value.verify_request.assert_called_with(ANY, scopes=[])
        self.verify_patcher.stop()
        self.oauth_patcher.stop()

    def assert_response_ok(self, response, data):
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', data)
        self.assertEqual(data['error'], None)
        self.assertIn('response', data)
        self.assertNotEqual(data['response'], None)


class K1APITest(K1APIBaseTest):
    def test_without_signature(self):
        self.test_signature = False
        self.mock_verify_oauth.return_value.verify_request.return_value = (False, None)
        test_paths = [up.name for up in urls.urlpatterns]
        for path in test_paths:
            self._test_signature(path)

    def _test_signature(self, path):
        response = self.client.get(
            reverse(path),
        )
        self.assertEqual(response.status_code, 401)
        response = self.client.get(
            reverse(path),
            TS_HEADER=str(int(time.time())),
            SIGNATURE_HEADER='abc'
        )
        self.assertEqual(response.status_code, 401)
