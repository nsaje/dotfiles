import django.test

import utils.url_helper


class CombineTrackingCodesTest(django.test.TestCase):

    def test_cobmine_tracking_codes(self):
        self.assertEqual(
            utils.url_helper.combine_tracking_codes('a=b', 'c=d'),
            'a=b&c=d'
        )

    def test_combine_tracking_codes_empty(self):
        self.assertEqual(
            utils.url_helper.combine_tracking_codes('', ''),
            ''
        )

        self.assertEqual(
            utils.url_helper.combine_tracking_codes('a=b', ''),
            'a=b'
        )

        self.assertEqual(
            utils.url_helper.combine_tracking_codes('a=b', '', 'c=d'),
            'a=b&c=d'
        )
