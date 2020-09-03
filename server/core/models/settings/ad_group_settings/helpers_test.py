from django.test import TestCase

from dash import constants

from . import helpers


class HelpersTestCase(TestCase):
    def test_get_browser_targeting_errors(self):
        device_types = [constants.AdTargetDevice.MOBILE, constants.AdTargetDevice.TABLET]
        target_browsers = [
            {"family": constants.BrowserFamily.CHROME},
            {"family": constants.BrowserFamily.IE},
            {"family": constants.BrowserFamily.FIREFOX},
        ]

        errors = helpers.get_browser_targeting_errors(target_browsers, device_types)
        self.assertEqual(errors, [{}, {"family": ["Invalid browser and device type combination configuration"]}, {}])

        device_types = [constants.AdTargetDevice.DESKTOP]
        target_browsers = [
            {"family": constants.BrowserFamily.CHROME},
            {"family": constants.BrowserFamily.IE},
            {"family": constants.BrowserFamily.FIREFOX},
        ]

        errors = helpers.get_browser_targeting_errors(target_browsers, device_types)
        self.assertEqual(errors, [{}, {}, {}])
