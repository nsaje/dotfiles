import json
import mock
import urllib2
import unittest

from django.test.client import RequestFactory

from utils import request_signer
from utils.test_decorators import integration_test


class EncryptionHelperTestCase(unittest.TestCase):

    def setUp(self):
        self.secret_key = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        self.factory = RequestFactory()

        self.url = 'https://example.com/test?hehe=lol'
        self.data = json.dumps({'aaaaa': 1111111})
        self.signature = '2OfzT_1GrqvcLTECicW3rCec4NXd6UGTXqlo1GV6PY4='

    @mock.patch('time.time')
    def test_sign(self, mock_time):
        mock_time.return_value = 123456789
        request = urllib2.Request(self.url, self.data)
        request_signer.sign_urllib2_request(request, self.secret_key)
        self.assertEqual(request.headers[request_signer.SIGNATURE_HEADER], self.signature)

    def test_sign_invalid_protocol(self):
        request = urllib2.Request('http://example.com', self.data)
        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib2_request(request, self.secret_key)

    def test_sign_invalid_key(self):
        request = urllib2.Request(self.url, self.data)

        request_signer.sign_urllib2_request(request, self.secret_key)

        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib2_request(request, None)

        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib2_request(request, '')

        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib2_request(request, 1234)

        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib2_request(request, 'short')

    @mock.patch('time.time')
    def test_verify(self, mock_time):
        mock_time.return_value = 123456789
        header_sig = request_signer._get_wsgi_header_field_name(
            request_signer.SIGNATURE_HEADER,
        )
        header_ts = request_signer._get_wsgi_header_field_name(
            request_signer.TS_HEADER,
        )

        request = self.factory.post(
            self.url,
            data=self.data,
            content_type='application/json',
            **{header_sig: self.signature, header_ts: str(mock_time())}
        )

        request_signer.verify_wsgi_request(request, self.secret_key)

    def test_missing_signature(self):
        request = self.factory.post(
            self.url,
            data=self.data,
            content_type='application/json',
        )

        with self.assertRaises(request_signer.SignatureError):
            request_signer.verify_wsgi_request(request, self.secret_key)

    def test_verify_invalid_signature(self):
        new_secret_key = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'

        request = self.factory.post(
            self.url,
            data=self.data,
            content_type='application/json',
            **{request_signer.SIGNATURE_HEADER.upper(): self.signature}
        )

        with self.assertRaises(request_signer.SignatureError):
            request_signer.verify_wsgi_request(request, new_secret_key)

    @integration_test
    def test_secure_open(self):
        request = urllib2.Request('https://one.zemanta.com', self.data)
        # one.zemanta.com returns 403 for post requests
        with self.assertRaises(urllib2.HTTPError):
            request_signer.urllib2_secure_open(request, self.secret_key)

        request = urllib2.Request('https://google.com', self.data)
        # certificate verify failed is url error
        with self.assertRaises(urllib2.URLError):
            request_signer.urllib2_secure_open(request, self.secret_key)
