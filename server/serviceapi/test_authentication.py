import urllib2
from django.test import TestCase
from django.test.client import RequestFactory

import authentication
import zemauth.models
from utils import request_signer


def urllib2_to_wsgi_request(request):
    header_sig = request_signer.get_wsgi_header_field_name(request_signer.SIGNATURE_HEADER)
    header_ts = request_signer.get_wsgi_header_field_name(request_signer.TS_HEADER)
    wsgi_request = RequestFactory().get(
        request.get_full_url(),
        **{header_sig: request.get_header(request_signer.SIGNATURE_HEADER),
           header_ts: request.get_header(request_signer.TS_HEADER)}
    )
    return wsgi_request


class TestAuthentication(TestCase):

    def test_gen_service_authentication(self):
        request = urllib2.Request(url='https://www.example.com/test?my=q')
        request_signer.sign_urllib2_request(request, 'aaaaaaaaaaaaaaaa')
        user = zemauth.models.User.objects.get_or_create_service_user('test-service')
        auth = authentication.gen_service_authentication('test-service', ['aaaaaaaaaaaaaaaa'])()

        wsgi_request = urllib2_to_wsgi_request(request)
        ret = auth.authenticate(wsgi_request)
        self.assertEqual(ret, (user, None))
