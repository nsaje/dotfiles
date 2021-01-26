import urllib.error
import urllib.parse
import urllib.request
from unittest import mock

from django.test import TestCase
from django.test.client import RequestFactory
from django.utils.timezone import now
from django.utils.timezone import timedelta
from oauth2_provider.models import AccessToken
from oauth2_provider.models import Application

import zemauth.models
from utils import request_signer

from . import authentication


def urllib2_to_wsgi_request(request):
    header_sig = request_signer.get_wsgi_header_field_name(request_signer.SIGNATURE_HEADER)
    header_ts = request_signer.get_wsgi_header_field_name(request_signer.TS_HEADER)
    wsgi_request = RequestFactory().get(
        request.get_full_url(),
        **{
            header_sig: request.get_header(request_signer.SIGNATURE_HEADER).decode("utf-8"),
            header_ts: request.get_header(request_signer.TS_HEADER),
        },
    )
    return wsgi_request


class TestServiceAuthentication(TestCase):
    def test_gen_service_authentication(self):
        request = urllib.request.Request(url="https://www.example.com/test?my=q")
        request_signer.sign_urllib_request(request, b"aaaaaaaaaaaaaaaa")
        user = zemauth.models.User.objects.get_or_create_service_user("test-service")
        auth = authentication.gen_service_authentication("test-service", [b"aaaaaaaaaaaaaaaa"])()

        wsgi_request = urllib2_to_wsgi_request(request)
        ret = auth.authenticate(wsgi_request)
        self.assertEqual(ret, (user, None))

    def test_gen_service_authentication_invalid(self):
        request = urllib.request.Request(url="https://www.example.com/test?my=q")
        request_signer.sign_urllib_request(request, b"aaaaaaaaaaaaaaab")
        auth = authentication.gen_service_authentication("test-service", [b"aaaaaaaaaaaaaaaa"])()

        wsgi_request = urllib2_to_wsgi_request(request)
        ret = auth.authenticate(wsgi_request)
        self.assertEqual(ret, None)

    @mock.patch.object(request_signer, "verify_wsgi_request")
    def test_gen_service_authentication_error(self, mock_verify):
        request = urllib.request.Request(url="https://www.example.com/test?my=q")
        request_signer.sign_urllib_request(request, b"aaaaaaaaaaaaaaaa")
        auth = authentication.gen_service_authentication("test-service", [b"aaaaaaaaaaaaaaaa"])()
        mock_verify.side_effect = Exception

        wsgi_request = urllib2_to_wsgi_request(request)
        with self.assertRaises(Exception):
            auth.authenticate(wsgi_request)


class TestOAuthServiceAuthentication(TestCase):
    def setUp(self):
        self.user = zemauth.models.User.objects.get_or_create_service_user("test-service")
        self.app = Application.objects.create(
            name="app",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            user=self.user,
        )
        self.token = AccessToken.objects.create(
            user=self.user, token="oauth-token", application=self.app, expires=now() + timedelta(days=365)
        )
        self.factory = RequestFactory()

    def test_gen_oauth_authentication_valid(self):
        auth_headers = {"HTTP_AUTHORIZATION": "Bearer " + "oauth-token"}
        request = self.factory.get("/some-url/", **auth_headers)

        backend = authentication.gen_oauth_authentication("test-service")()
        credentials = {"request": request}
        u, _ = backend.authenticate(**credentials)
        self.assertEqual(u, self.user)

    def test_gen_oauth_authentication_invalid_token(self):
        auth_headers = {"HTTP_AUTHORIZATION": "Bearer " + "invalid-token"}
        request = self.factory.get("/some-url/", **auth_headers)

        backend = authentication.gen_oauth_authentication("test-service")()
        credentials = {"request": request}
        self.assertEqual(backend.authenticate(**credentials), None)

    def test_gen_oauth_authentication_invalid_user(self):
        auth_headers = {"HTTP_AUTHORIZATION": "Bearer " + "oauth-token"}
        request = self.factory.get("/some-url/", **auth_headers)

        backend = authentication.gen_oauth_authentication("invalid-service")()
        credentials = {"request": request}
        self.assertEqual(backend.authenticate(**credentials), None)
