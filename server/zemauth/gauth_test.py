from django import test
import mock

from zemauth import gauth

SETTINGS = {
    'GOOGLE_OAUTH_CLIENT_ID': '1111.apps.googleusercontent.com',
    'GOOGLE_OAUTH_CLIENT_SECRET': '111111111111111111111111'
}


class GauthTestCase(test.TestCase):
    def test_get_flow(self):
        with self.settings(**SETTINGS):
            request = mock.Mock()
            request.build_absolute_uri.return_value = 'http://test.zemanta.com/'
            request.GET = {'next': '/v2/analytics/adgroup/1'}

            flow = gauth.get_flow(request)

            expected = 'https://accounts.google.com/o/oauth2/v2/auth?state=%2Fv2%2Fanalytics%2Fadgroup%2F1&redirect_uri=https%3A%2F%2Ftest.zemanta.com%2F&response_type=code&client_id=1111.apps.googleusercontent.com&scope=email&access_type=online'
            self.assertEqual(flow.step1_get_authorize_url(), expected)

    def test_get_uri(self):
        with self.settings(**SETTINGS):
            request = mock.Mock()
            request.build_absolute_uri.return_value = 'http://test.zemanta.com/'
            request.GET = {'next': '/v2/analytics/adgroup/1'}

            flow = gauth.get_flow(request)

            expected = 'https://accounts.google.com/o/oauth2/v2/auth?state=%2Fv2%2Fanalytics%2Fadgroup%2F1&redirect_uri=https%3A%2F%2Ftest.zemanta.com%2F&response_type=code&client_id=1111.apps.googleusercontent.com&scope=email&access_type=online'
            self.assertEqual(gauth.get_uri(request, flow), expected)
