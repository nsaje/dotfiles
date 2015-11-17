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
