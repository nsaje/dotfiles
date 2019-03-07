from django import test
from django.urls import exceptions
from django.urls import reverse


class UrlsTest(test.TestCase):
    def test_invalid_url(self):
        with self.assertRaises(exceptions.NoReverseMatch):
            reverse("bid_modifiers_upload", kwargs={"ad_group_id": 1, "modifier_type": "INVALID"})

    def test_no_modifier_type(self):
        with self.assertRaises(exceptions.NoReverseMatch):
            reverse("bid_modifiers_upload", kwargs={"ad_group_id": 1})
