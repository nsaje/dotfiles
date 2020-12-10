from django.test import TestCase
from django.test import override_settings
from mock import Mock
from mock import patch

import dash.models

from . import client


@override_settings(
    R1_PIXEL_URL="https://r1.example.com/api/pixel/{account_id}/{slug}/",
    R1_API_SIGN_KEY=b"AAAAAAAAAAAAAAAAAAAAAAAA",
    R1_DEMO_MODE=False,
)
@patch("utils.request_signer._secure_opener.open")
class UpdatePixelTestCase(TestCase):
    fixtures = ["test_k1_api.yaml"]

    def test_update_pixel(self, mock_urlopen):
        response = Mock()
        response.read.return_value = '{"status": "ok"}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        conversion_pixel = dash.models.ConversionPixel.objects.get(pk=1)
        conversion_pixel.redirect_url = "http://test.com"
        client.update_pixel(conversion_pixel)

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), "https://r1.example.com/api/pixel/1/testslug1/")
        self.assertEqual(call.get_method(), "PUT")
        expected = {"redirecturl": "http://test.com"}
        self.assertJSONEqual(call.data, expected)

    def test_update_pixel_error(self, mock_urlopen):
        response = Mock()
        response.getcode = lambda: 400
        mock_urlopen.return_value = response

        conversion_pixel = dash.models.ConversionPixel.objects.get(pk=1)
        with self.assertRaises(Exception):
            client.update_pixel(conversion_pixel)

        self.assertEqual(len(mock_urlopen.call_args_list), 3, "Should retry the call 3-times")
