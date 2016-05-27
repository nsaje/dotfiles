from mock import patch
from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse


class LambdaCallbackApiTest(TestCase):

    @patch('utils.request_signer.verify_wsgi_request')
    @override_settings(LAMBDA_CONTENT_UPLOAD_SIGN_KEY='key')
    def test_content_upload_callback(self, mock_verify_wsgi_request):
        response = self.client.post(
            reverse('lambdas.content_upload_callback')
        )
        mock_verify_wsgi_request.called_with(response.wsgi_request, 'key')
        self.assertEqual(response.json(), { 'status': 'ok' })
