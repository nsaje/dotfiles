import rest_framework.serializers
from django.test import TestCase

import dash.constants

from . import validators


class ValidatorsTestCase(TestCase):
    def test_validate_ad_width(self):
        self.assertIsNone(validators.validate_ad_width(None))
        self.assertIsNone(validators.validate_ad_width(dash.constants.DisplayAdSize.BANNER[0]))
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_width(-1)
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_width(0)
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_width("invalid")

    def test_validate_ad_height(self):
        self.assertIsNone(validators.validate_ad_height(None))
        self.assertIsNone(validators.validate_ad_height(dash.constants.DisplayAdSize.BANNER[1]))
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_height(-1)
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_height(0)
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_height("invalid")

    def test_validate_ad_size_variants(self):
        self.assertIsNone(validators.validate_ad_size_variants(None, None))
        self.assertIsNone(
            validators.validate_ad_size_variants(
                dash.constants.DisplayAdSize.BANNER[0], dash.constants.DisplayAdSize.BANNER[1]
            )
        )
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_size_variants(
                dash.constants.DisplayAdSize.BANNER[0], dash.constants.DisplayAdSize.HALF_PAGE[1]
            )
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_size_variants(-1, -1)
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_size_variants(0, 0)
        with self.assertRaises(rest_framework.serializers.ValidationError):
            validators.validate_ad_size_variants("invalid", "invalid")
