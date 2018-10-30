import urllib.parse

from django.conf import settings
from django.test import TestCase

from utils import url_helper


class CombineTrackingCodesTest(TestCase):
    def test_cobmine_tracking_codes(self):
        self.assertEqual(url_helper.combine_tracking_codes("a=b", "c=d"), "a=b&c=d")

    def test_combine_tracking_codes_empty(self):
        self.assertEqual(url_helper.combine_tracking_codes("", ""), "")

        self.assertEqual(url_helper.combine_tracking_codes("a=b", ""), "a=b")

        self.assertEqual(url_helper.combine_tracking_codes("a=b", "", "c=d"), "a=b&c=d")


class GetURLTest(TestCase):
    def test_get_full_z1_url(self):
        url = url_helper.get_full_z1_url("abcd/123")

        self.assertEqual(url, urllib.parse.urljoin(settings.BASE_URL, "/abcd/123"))
