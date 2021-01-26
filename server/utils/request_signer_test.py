import json
import unittest
import urllib.error
import urllib.request
from unittest import mock

from django.test.client import RequestFactory

from utils import request_signer
from utils.test_decorators import integration_test


class EncryptionHelperTestCase(unittest.TestCase):
    def setUp(self):
        self.secret_key = b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        self.factory = RequestFactory()

        self.url = "https://example.com/test?hehe=lol"
        self.data = json.dumps({"aaaaa": 1111111}).encode("utf-8")
        self.signature = b"2OfzT_1GrqvcLTECicW3rCec4NXd6UGTXqlo1GV6PY4="

    @mock.patch("time.time")
    def test_sign(self, mock_time):
        mock_time.return_value = 123456789
        request = urllib.request.Request(self.url, self.data)
        request_signer.sign_urllib_request(request, self.secret_key)
        self.assertEqual(request.headers[request_signer.SIGNATURE_HEADER], self.signature)

    def test_sign_invalid_protocol(self):
        request = urllib.request.Request("http://example.com", self.data)
        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib_request(request, self.secret_key)

    def test_sign_invalid_key(self):
        request = urllib.request.Request(self.url, self.data)

        request_signer.sign_urllib_request(request, self.secret_key)

        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib_request(request, None)

        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib_request(request, "")

        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib_request(request, 1234)

        with self.assertRaises(request_signer.SignatureError):
            request_signer.sign_urllib_request(request, "short")

    @mock.patch("time.time")
    def test_verify(self, mock_time):
        mock_time.return_value = 123456789
        header_sig = request_signer.get_wsgi_header_field_name(request_signer.SIGNATURE_HEADER)
        header_ts = request_signer.get_wsgi_header_field_name(request_signer.TS_HEADER)

        request = self.factory.post(
            self.url,
            data=self.data,
            content_type="application/json",
            **{header_sig: self.signature.decode("utf-8"), header_ts: str(mock_time())},
        )

        request_signer.verify_wsgi_request(request, [b"my-deprecated-key", self.secret_key])

    @mock.patch("time.time")
    def test_verify_invalid_timestamp(self, mock_time):
        mock_time.return_value = 987654321
        header_sig = request_signer.get_wsgi_header_field_name(request_signer.SIGNATURE_HEADER)
        header_ts = request_signer.get_wsgi_header_field_name(request_signer.TS_HEADER)

        request = self.factory.post(
            self.url,
            data=self.data,
            content_type="application/json",
            **{header_sig: self.signature, header_ts: "123456789"},
        )

        with self.assertRaises(request_signer.SignatureError):
            request_signer.verify_wsgi_request(request, self.secret_key)

    def test_missing_signature(self):
        request = self.factory.post(self.url, data=self.data, content_type="application/json")

        with self.assertRaises(request_signer.SignatureError):
            request_signer.verify_wsgi_request(request, self.secret_key)

    def test_verify_invalid_signature(self):
        new_secret_key = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

        request = self.factory.post(
            self.url,
            data=self.data,
            content_type="application/json",
            **{request_signer.SIGNATURE_HEADER.upper(): self.signature},
        )

        with self.assertRaises(request_signer.SignatureError):
            request_signer.verify_wsgi_request(request, new_secret_key)

    @integration_test
    def test_secure_open(self):
        request = urllib.request.Request("https://one.zemanta.com", self.data)
        # one.zemanta.com returns 403 for post requests
        with self.assertRaises(urllib.error.HTTPError):
            request_signer.urllib_secure_open(request, self.secret_key)

        request = urllib.request.Request("https://google.com", self.data)
        # certificate verify failed is url error
        with self.assertRaises(urllib.error.URLError):
            request_signer.urllib_secure_open(request, self.secret_key)
