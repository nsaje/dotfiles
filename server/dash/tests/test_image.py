import json
from mock import patch, Mock

from django.test import TestCase, override_settings
from django.conf import settings

from dash import image


@override_settings(
    Z3_API_URL='http://z3.example.com',
)
class ImageTest(TestCase):
    @patch('utils.pagerduty_helper.urllib2.urlopen')
    def test_process_image(self, mock_urlopen):
        url = 'http://example.com/image'
        crop_areas = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
        image_id = 'test_image_id'

        response = Mock()
        response.read.return_value = '{"key": "%s"}' % image_id
        mock_urlopen.return_value = response

        self.assertEqual(image.process_image(url, crop_areas), image_id)

        mock_urlopen.assert_called_with(
            settings.Z3_API_URL,
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
                'image-url': 'http://example.com/image'
            })
        )
