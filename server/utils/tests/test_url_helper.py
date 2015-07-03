from django.test import TestCase

from utils import url_helper


class CombineTrackingCodesTest(TestCase):

    def test_cobmine_tracking_codes(self):
        self.assertEqual(
            url_helper.combine_tracking_codes('a=b', 'c=d'),
            'a=b&c=d'
        )

    def test_combine_tracking_codes_empty(self):
        self.assertEqual(
            url_helper.combine_tracking_codes('', ''),
            ''
        )

        self.assertEqual(
            url_helper.combine_tracking_codes('a=b', ''),
            'a=b'
        )

        self.assertEqual(
            url_helper.combine_tracking_codes('a=b', '', 'c=d'),
            'a=b&c=d'
        )


class AddTrackingCodesToUrlTest(TestCase):
    def test(self):
        url = 'http://example.com/?param3=ccc'
        tracking_codes = 'param1=aaa&param2=bbb'

        result = url_helper.add_tracking_codes_to_url(url, tracking_codes)

        self.assertEqual(result, 'http://example.com/?param3=ccc&param1=aaa&param2=bbb')

    def test_no_tracking_codes(self):
        url = 'http://example.com/?param3=ccc'
        tracking_codes = None

        result = url_helper.add_tracking_codes_to_url(url, tracking_codes)

        self.assertEqual(result, url)


class GetTrackingIdParamsTest(TestCase):
    def test(self):
        ad_group_id = 1
        tracking_slug = 'test_slug'

        result = url_helper.get_tracking_id_params(ad_group_id, tracking_slug)

        self.assertEqual(result, '_z1_adgid=1&_z1_msid=test_slug')

    def test_no_tracking_slug(self):
        ad_group_id = 1
        tracking_slug = None

        result = url_helper.get_tracking_id_params(ad_group_id, tracking_slug)

        self.assertEqual(result, '_z1_adgid=1')
