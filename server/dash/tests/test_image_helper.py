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
