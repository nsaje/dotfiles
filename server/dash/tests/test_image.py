import json
from mock import patch, Mock

from django.test import TestCase, override_settings
from django.conf import settings

from dash import image


@override_settings(
    Z3_API_IMAGE_URL='http://z3.example.com',
)
@patch('utils.pagerduty_helper.urllib2.urlopen')
class ImageTest(TestCase):
    def test_process_image(self, mock_urlopen):
        url = 'http://example.com/image'
        crop_areas = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
        image_id = 'test_image_id'

        response = Mock()
        response.read.return_value = '{"key": "%s", "status": "success"}' % image_id
        response.code = 200
        mock_urlopen.return_value = response

        self.assertEqual(image.process_image(url, crop_areas), image_id)

        mock_urlopen.assert_called_with(
            settings.Z3_API_IMAGE_URL,
            json.dumps({
                'crops': {
                    'square': {
                        'tl': {'y': 2, 'x': 1},
                        'br': {'y': 4, 'x': 3}
                    },
                    'landscape': {
                        'tl': {'y': 6, 'x': 5},
                        'br': {'y': 8, 'x': 7}
                    }
                },
                'image_url': 'http://example.com/image',
                'image-url': 'http://example.com/image'
            })
        )

    def test_code_error(self, mock_urlopen):
        url = 'http://example.com/image'

        response = Mock()
        response.code = 500
        mock_urlopen.return_value = response

        with self.assertRaises(image.ImageProcessingException):
            image.process_image(url, None)

    def test_status_not_success(self, mock_urlopen):
        url = 'http://example.com/image'
        image_id = 'test_image_id'

        response = Mock()
        response.read.return_value = '{"key": "%s", "status": "error"}' % image_id
        mock_urlopen.return_value = response

        with self.assertRaises(image.ImageProcessingException):
            image.process_image(url, None)

    def test_status_key_empty(self, mock_urlopen):
        url = 'http://example.com/image'

        response = Mock()
        response.read.return_value = '{"key": "", "status": "error"}'
        mock_urlopen.return_value = response

        with self.assertRaises(image.ImageProcessingException):
            image.process_image(url, None)
