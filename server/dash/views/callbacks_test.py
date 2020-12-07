import json

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from mock import patch

from dash.features import contentupload


class LambdaCallbackApiTest(TestCase):
    def setUp(self):
        self.candidate = {
            "id": 1,
            "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
            "image": {
                "width": 1500,
                "hash": "0000000000000000",
                "id": "demo/demo-123/srv/some-batch/31eb9a632e3547039169d1b650155e14",
                "height": 245,
            },
            "valid": True,
            "targetUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
        }

    @patch("dash.features.contentupload.upload.process_callback")
    @patch("utils.request_signer.verify_wsgi_request")
    @override_settings(LAMBDA_CONTENT_UPLOAD_SIGN_KEY="key")
    def test_content_upload_callback(self, mock_verify_wsgi_request, mock_process_callback):
        response = self.client.post(
            reverse("callbacks.content_upload"),
            json.dumps({"status": "ok", "candidate": self.candidate}),
            "application/json",
        )
        mock_verify_wsgi_request.called_with(response.wsgi_request, "key")
        mock_process_callback.called_with(self.candidate)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("dash.features.contentupload.upload.process_callback")
    @patch("utils.request_signer.verify_wsgi_request")
    @override_settings(LAMBDA_CONTENT_UPLOAD_SIGN_KEY="key")
    def test_content_upload_callback_lambda_fail(self, mock_verify_wsgi_request, mock_process_callback):

        response = self.client.post(
            reverse("callbacks.content_upload"),
            json.dumps({"status": "fail", "candidate": self.candidate}),
            "application/json",
        )
        mock_verify_wsgi_request.called_with(response.wsgi_request, "key")
        self.assertFalse(mock_process_callback.called)
        self.assertEqual(response.json(), {"status": "fail"})

    @patch("dash.features.contentupload.upload.process_callback")
    @patch("utils.request_signer.verify_wsgi_request")
    @override_settings(LAMBDA_CONTENT_UPLOAD_SIGN_KEY="key")
    def test_content_upload_callback_candidate_doesnt_exist(self, mock_verify_wsgi_request, mock_process_callback):
        mock_process_callback.side_effect = contentupload.upload.exc.CandidateDoesNotExist()
        response = self.client.post(
            reverse("callbacks.content_upload"),
            json.dumps({"status": "ok", "candidate": self.candidate}),
            "application/json",
        )
        mock_verify_wsgi_request.called_with(response.wsgi_request, "key")
        self.assertTrue(mock_process_callback.called)
        self.assertEqual(response.json(), {"status": "fail"})
