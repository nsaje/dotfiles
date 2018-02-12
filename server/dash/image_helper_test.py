import datetime
import time

from mock import patch
from django.test import TestCase, override_settings

from dash import image_helper


@override_settings(
    IMAGE_THUMBNAIL_URL='http://test.com'
)
class GetImageUrlTest(TestCase):

    def test_get_image_url(self):
        image_url = image_helper.get_image_url('foo', 500, 600, 'center')
        self.assertEqual(image_url, 'http://test.com/foo.jpg?w=500&h=600&fit=crop&crop=center&fm=jpg')

        image_url = image_helper.get_image_url(None, 500, 600, 'center')
        self.assertEqual(image_url, None)

        image_url = image_helper.get_image_url('foo', None, 600, 'center')
        self.assertEqual(image_url, None)

        image_url = image_helper.get_image_url('foo', 500, None, 'center')
        self.assertEqual(image_url, None)

        image_url = image_helper.get_image_url('foo', 500, 600, None)
        self.assertEqual(image_url, None)


@override_settings(
    IMAGE_THUMBNAIL_URL='http://test.com'
)
class UploadImageToS3(TestCase):

    @patch('time.time')
    @patch('random.randint')
    def test_upload_image_to_s3(self, mock_randint, mock_time):
        mock_randint.return_value = 99999
        mock_time.return_value = time.mktime(datetime.datetime(2016, 9, 1).timetuple())
        image = open('./dash/test_files/test.jpg', 'rb')
        batch_id = 1234

        key = image_helper.upload_image_to_s3(image, batch_id)
        self.assertEqual('http://test.com/u/1234/147268800000099999.jpg', key)
