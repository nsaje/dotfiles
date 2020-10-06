import mock
from django.test import TestCase

import core.models
from dash import constants as dash_constants
from dash import publisher_helpers
from dash.features import geolocation
from utils.magic_mixer import magic_mixer

from . import constants
from . import converters
from . import exceptions


class TestTargetConverter(TestCase):
    def setUp(self):
        self.converter = converters.TargetConverter

    def test_invalid_modifier_type(self):
        with self.assertRaises(exceptions.BidModifierTypeInvalid):
            self.converter.to_target(1234, None)

        with self.assertRaises(exceptions.BidModifierTypeInvalid):
            self.converter.from_target(1234, None)

    def test_publisher(self):
        # full circle test
        publisher_domain = "example.com"

        output_value = self.converter.from_target(constants.BidModifierType.PUBLISHER, publisher_domain)
        self.assertEqual(output_value, publisher_domain)

        target_value = self.converter.to_target(constants.BidModifierType.PUBLISHER, output_value)
        self.assertEqual(target_value, publisher_domain)

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.PUBLISHER, "")
        self.assertEqual(str(ctx.exception), "Publisher should not be empty")

    def test_placement(self):
        # full circle test
        source = magic_mixer.blend(core.models.Source, name="Outbrain", bidder_slug="b1_outbrain")
        publisher_domain = "example.com"
        placement = "100001-1001633"

        placement_id = publisher_helpers.create_placement_id(publisher_domain, source.id, placement)

        output_value = self.converter.from_target(constants.BidModifierType.PLACEMENT, placement_id)
        self.assertEqual(output_value, placement_id)

        target_value = self.converter.to_target(constants.BidModifierType.PLACEMENT, output_value)
        self.assertEqual(target_value, placement_id)

        with self.assertRaisesMessage(exceptions.BidModifierTargetInvalid, "Invalid Placement Target"):
            self.converter.to_target(constants.BidModifierType.PLACEMENT, "")

        with self.assertRaisesMessage(exceptions.BidModifierTargetInvalid, "Invalid Placement Target"):
            self.converter.to_target(constants.BidModifierType.PLACEMENT, f"{publisher_domain}__{source.id}__")

        with self.assertRaisesMessage(exceptions.BidModifierTargetInvalid, "Invalid Placement Target"):
            self.converter.to_target(
                constants.BidModifierType.PLACEMENT, f"{publisher_domain}__{source.id}__Not reported"
            )

        with self.assertRaisesMessage(exceptions.BidModifierTargetInvalid, "Invalid Source"):
            self.converter.to_target(constants.BidModifierType.PLACEMENT, f"{publisher_domain}__-1__{placement}")

    def test_source(self):
        # full circle test
        source = magic_mixer.blend(core.models.Source, name="Outbrain", bidder_slug="b1_outbrain")

        output_value = self.converter.from_target(constants.BidModifierType.SOURCE, str(source.id))
        self.assertEqual(output_value, source.bidder_slug)

        target_value = self.converter.to_target(constants.BidModifierType.SOURCE, output_value)
        self.assertEqual(target_value, str(source.id))

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.SOURCE, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Source")

    def test_device_type(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.DEVICE, str(dash_constants.DeviceType.MOBILE)
        )
        self.assertEqual(output_value, dash_constants.DeviceType.get_name(dash_constants.DeviceType.MOBILE))

        target_value = self.converter.to_target(constants.BidModifierType.DEVICE, output_value)
        self.assertEqual(target_value, str(dash_constants.DeviceType.MOBILE))

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.DEVICE, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.DEVICE, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.DEVICE, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Device Type")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.DEVICE, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Device Type")

    def test_operating_system(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.OPERATING_SYSTEM, dash_constants.OperatingSystem.MACOSX
        )
        self.assertEqual(output_value, dash_constants.OperatingSystem.get_name(dash_constants.OperatingSystem.MACOSX))

        target_value = self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, output_value)
        self.assertEqual(target_value, dash_constants.OperatingSystem.MACOSX)

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.OPERATING_SYSTEM, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.OPERATING_SYSTEM, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Operating System")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Operating System")

    def test_environment(self):
        # full circle test
        output_value = self.converter.from_target(constants.BidModifierType.ENVIRONMENT, dash_constants.Environment.APP)
        self.assertEqual(output_value, dash_constants.Environment.get_name(dash_constants.Environment.APP))

        target_value = self.converter.to_target(constants.BidModifierType.ENVIRONMENT, output_value)
        self.assertEqual(target_value, dash_constants.Environment.APP)

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.ENVIRONMENT, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.ENVIRONMENT, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.ENVIRONMENT, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Environment")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.ENVIRONMENT, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Environment")

    def test_country(self):
        # full circle test
        geo_location = magic_mixer.blend(
            geolocation.Geolocation, key="US", type=dash_constants.LocationType.COUNTRY, name="United States"
        )

        output_value = self.converter.from_target(constants.BidModifierType.COUNTRY, geo_location.key)
        self.assertEqual(output_value, geo_location.key)

        target_value = self.converter.to_target(constants.BidModifierType.COUNTRY, output_value)
        self.assertEqual(target_value, geo_location.key)

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.COUNTRY, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Geolocation")

    def test_state(self):
        # full circle test
        geo_location = magic_mixer.blend(
            geolocation.Geolocation, key="US-TX", type=dash_constants.LocationType.REGION, name="Texas, United States"
        )

        output_value = self.converter.from_target(constants.BidModifierType.STATE, geo_location.key)
        self.assertEqual(output_value, geo_location.key)

        target_value = self.converter.to_target(constants.BidModifierType.STATE, output_value)
        self.assertEqual(target_value, geo_location.key)

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.STATE, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Geolocation")

    def test_dma(self):
        # full circle test
        geo_location = magic_mixer.blend(
            geolocation.Geolocation, key="765", type=dash_constants.LocationType.DMA, name="765 El Paso, TX"
        )

        output_value = self.converter.from_target(constants.BidModifierType.DMA, geo_location.key)
        self.assertEqual(output_value, geo_location.key)

        target_value = self.converter.to_target(constants.BidModifierType.DMA, output_value)
        self.assertEqual(target_value, geo_location.key)

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.DMA, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Geolocation")

    def test_content_ad(self):
        # full circle test
        content_ad = magic_mixer.blend(core.models.ContentAd)

        output_value = self.converter.from_target(constants.BidModifierType.AD, str(content_ad.id))
        self.assertEqual(output_value, str(content_ad.id))

        target_value = self.converter.to_target(constants.BidModifierType.AD, output_value)
        self.assertEqual(target_value, str(content_ad.id))

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.AD, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Content Ad")

    def test_browser(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.BROWSER, dash_constants.BrowserFamily.CHROME
        )
        self.assertEqual(output_value, dash_constants.BrowserFamily.get_name(dash_constants.BrowserFamily.CHROME))

        target_value = self.converter.to_target(constants.BidModifierType.BROWSER, output_value)
        self.assertEqual(target_value, dash_constants.BrowserFamily.CHROME)

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.BROWSER, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.BROWSER, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.BROWSER, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Browser Family")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.BROWSER, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Browser Family")

    def test_connection_type(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.CONNECTION_TYPE, dash_constants.ConnectionType.WIFI
        )
        self.assertEqual(output_value, dash_constants.ConnectionType.get_name(dash_constants.ConnectionType.WIFI))

        target_value = self.converter.to_target(constants.BidModifierType.CONNECTION_TYPE, output_value)
        self.assertEqual(target_value, dash_constants.ConnectionType.WIFI)

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.CONNECTION_TYPE, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.CONNECTION_TYPE, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.CONNECTION_TYPE, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Connection Type")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.CONNECTION_TYPE, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Connection Type")


class TestFileConverter(TestCase):
    def setUp(self):
        self.converter = converters.FileConverter

    def test_source(self):
        # full circle test
        source = magic_mixer.blend(core.models.Source, name="Outbrain", bidder_slug="b1_outbrain")

        output_value = self.converter.from_target(constants.BidModifierType.SOURCE, str(source.id))
        self.assertEqual(output_value, source.bidder_slug)

        target_value = self.converter.to_target(constants.BidModifierType.SOURCE, output_value)
        self.assertEqual(target_value, str(source.id))

        # illegal target value tests
        with self.assertRaises(ValueError):
            self.converter.from_target(constants.BidModifierType.SOURCE, "invalid")

        with self.assertRaises(AttributeError):
            self.converter.from_target(constants.BidModifierType.SOURCE, "-1")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.SOURCE, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Source")

    def test_operating_system(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.OPERATING_SYSTEM, dash_constants.OperatingSystem.MACOSX
        )
        self.assertEqual(output_value, dash_constants.OperatingSystem.get_name(dash_constants.OperatingSystem.MACOSX))

        target_value = self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, output_value)
        self.assertEqual(target_value, dash_constants.OperatingSystem.MACOSX)

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.OPERATING_SYSTEM, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.OPERATING_SYSTEM, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Operating System")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Operating System")

        # legacy full circle test
        target_value = self.converter.to_target(
            constants.BidModifierType.OPERATING_SYSTEM,
            dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.MACOSX),
        )
        self.assertEqual(target_value, dash_constants.OperatingSystem.MACOSX)


class TestDashboardConverter(TestCase):
    def setUp(self):
        self.converter = converters.DashboardConverter

    def test_device_type(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.DEVICE, str(dash_constants.DeviceType.MOBILE)
        )
        self.assertEqual(output_value, dash_constants.DeviceType.MOBILE)

        target_value = self.converter.to_target(constants.BidModifierType.DEVICE, output_value)
        self.assertEqual(target_value, str(dash_constants.DeviceType.MOBILE))

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.DEVICE, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.DEVICE, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.DEVICE, "invalid")
            self.assertEqual(str(ctx.exception), "Invalid Device Type")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.DEVICE, 1234)
            self.assertEqual(str(ctx.exception), "Invalid Device Type")

    def test_operating_system(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.OPERATING_SYSTEM, dash_constants.OperatingSystem.MACOSX
        )
        self.assertEqual(output_value, dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.MACOSX))

        target_value = self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, output_value)
        self.assertEqual(target_value, dash_constants.OperatingSystem.MACOSX)

        # special case full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.OPERATING_SYSTEM, dash_constants.OperatingSystem.WINPHONE
        )
        self.assertEqual(output_value, "WinPhone")

        target_value = self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, output_value)
        self.assertEqual(target_value, dash_constants.OperatingSystem.WINPHONE)

        # illegal target value tests
        with self.assertRaises(ValueError):
            self.converter.from_target(constants.BidModifierType.OPERATING_SYSTEM, 1234)

        with self.assertRaises(ValueError):
            self.converter.from_target(constants.BidModifierType.OPERATING_SYSTEM, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Operating System")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Operating System")

    def test_environment(self):
        # full circle test
        output_value = self.converter.from_target(constants.BidModifierType.ENVIRONMENT, dash_constants.Environment.APP)
        self.assertEqual(output_value, dash_constants.Environment.APP)

        target_value = self.converter.to_target(constants.BidModifierType.ENVIRONMENT, output_value)
        self.assertEqual(target_value, dash_constants.Environment.APP)

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.ENVIRONMENT, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.ENVIRONMENT, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.ENVIRONMENT, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Environment")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.ENVIRONMENT, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Environment")

    def test_dma(self):
        # full circle test
        geo_location = magic_mixer.blend(
            geolocation.Geolocation, key="765", type=dash_constants.LocationType.DMA, name="765 El Paso, TX"
        )

        output_value = self.converter.from_target(constants.BidModifierType.DMA, geo_location.key)
        self.assertEqual(output_value, int(geo_location.key))

        target_value = self.converter.to_target(constants.BidModifierType.DMA, output_value)
        self.assertEqual(target_value, geo_location.key)

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.DMA, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Geolocation")

    def test_source(self):
        test_source_name = "Test Source"
        source = magic_mixer.blend(core.models.Source, name=test_source_name)

        output_value = self.converter.from_target(constants.BidModifierType.SOURCE, source.id)
        self.assertEqual(source.name, output_value)

        target_value = self.converter.to_target(constants.BidModifierType.SOURCE, test_source_name)
        self.assertEqual(str(source.id), target_value)

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.SOURCE, "Non existing source")
        self.assertEqual(str(ctx.exception), "Invalid Source")

        magic_mixer.blend(core.models.Source, name=test_source_name)
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.SOURCE, test_source_name)
        self.assertEqual(str(ctx.exception), "Invalid Source")

    def test_browser(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.BROWSER, dash_constants.BrowserFamily.CHROME
        )
        self.assertEqual(output_value, dash_constants.BrowserFamily.CHROME)

        target_value = self.converter.to_target(constants.BidModifierType.BROWSER, output_value)
        self.assertEqual(target_value, dash_constants.BrowserFamily.CHROME)

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.BROWSER, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.BROWSER, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.BROWSER, "invalid")
            self.assertEqual(str(ctx.exception), "Invalid Browser Family")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.BROWSER, 1234)
            self.assertEqual(str(ctx.exception), "Invalid Browser Family")

    def test_connection_type(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.CONNECTION_TYPE, dash_constants.ConnectionType.WIFI
        )
        self.assertEqual(output_value, dash_constants.ConnectionType.WIFI)

        target_value = self.converter.to_target(constants.BidModifierType.CONNECTION_TYPE, output_value)
        self.assertEqual(target_value, dash_constants.ConnectionType.WIFI)

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.CONNECTION_TYPE, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.CONNECTION_TYPE, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.CONNECTION_TYPE, "invalid")
            self.assertEqual(str(ctx.exception), "Invalid Connection Type")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.CONNECTION_TYPE, 1234)
            self.assertEqual(str(ctx.exception), "Invalid Connection Type")


class TestStatsConverter(TestCase):
    def setUp(self):
        self.converter = converters.StatsConverter

    def test_target(self):
        target_converter = core.features.bid_modifiers.converters.TargetConverter
        test_cases = [
            {"type": constants.BidModifierType.AD, "to": "_to_content_ad_target", "from": "_from_content_ad_target"},
            {
                "type": constants.BidModifierType.PUBLISHER,
                "to": "_to_publisher_target",
                "from": "_from_publisher_target",
            },
            {"type": constants.BidModifierType.COUNTRY, "to": "_to_country_target", "from": "_from_country_target"},
            {"type": constants.BidModifierType.STATE, "to": "_to_state_target", "from": "_from_state_target"},
            {"type": constants.BidModifierType.DMA, "to": "_to_dma_target", "from": "_from_dma_target"},
        ]
        for test_case in test_cases:
            with mock.patch.object(target_converter, test_case["to"]) as mock_to_target:
                self.converter.to_target(test_case["type"], 1)
                mock_to_target.assert_called_once_with(1, test_case["type"])

            with mock.patch.object(target_converter, test_case["from"]) as mock_from_target:
                self.converter.from_target(test_case["type"], 1)
                mock_from_target.assert_called_once_with(1, test_case["type"])

    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._to_constant_target")
    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._from_constant_target")
    def test_device(self, mock_to_target, mock_from_target):
        self.converter.to_target(constants.BidModifierType.DEVICE, 1)
        self.converter.from_target(constants.BidModifierType.DEVICE, 1)
        mock_to_target.assert_called_once_with(1, constants.BidModifierType.DEVICE)
        mock_from_target.assert_called_once_with(1, constants.BidModifierType.DEVICE)

    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._to_operating_system_target")
    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._from_operating_system_target")
    def test_operating_system(self, mock_to_target, mock_from_target):
        self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, 1)
        self.converter.from_target(constants.BidModifierType.OPERATING_SYSTEM, 1)
        mock_to_target.assert_called_once_with(1, constants.BidModifierType.OPERATING_SYSTEM)
        mock_from_target.assert_called_once_with(1, constants.BidModifierType.OPERATING_SYSTEM)

    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._to_constant_target")
    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._from_constant_target")
    def test_environment(self, mock_to_target, mock_from_target):
        self.converter.to_target(constants.BidModifierType.ENVIRONMENT, 1)
        self.converter.from_target(constants.BidModifierType.ENVIRONMENT, 1)
        mock_to_target.assert_called_once_with(1, constants.BidModifierType.ENVIRONMENT)
        mock_from_target.assert_called_once_with(1, constants.BidModifierType.ENVIRONMENT)

    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._to_constant_target")
    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._from_constant_target")
    def test_browser(self, mock_to_target, mock_from_target):
        self.converter.to_target(constants.BidModifierType.BROWSER, 1)
        self.converter.from_target(constants.BidModifierType.BROWSER, 1)
        mock_to_target.assert_called_once_with(1, constants.BidModifierType.BROWSER)
        mock_from_target.assert_called_once_with(1, constants.BidModifierType.BROWSER)

    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._to_constant_target")
    @mock.patch("core.features.bid_modifiers.converters.DashboardConverter._from_constant_target")
    def test_connection_type(self, mock_to_target, mock_from_target):
        self.converter.to_target(constants.BidModifierType.CONNECTION_TYPE, 1)
        self.converter.from_target(constants.BidModifierType.CONNECTION_TYPE, 1)
        mock_to_target.assert_called_once_with(1, constants.BidModifierType.CONNECTION_TYPE)
        mock_from_target.assert_called_once_with(1, constants.BidModifierType.CONNECTION_TYPE)

    def test_source(self):
        source = magic_mixer.blend(core.models.Source)
        resolved_to_target = self.converter.to_target(constants.BidModifierType.SOURCE, source.id)
        self.assertEqual(resolved_to_target, str(source.id))

        resolved_from_target = self.converter.from_target(constants.BidModifierType.SOURCE, source.id)
        self.assertEqual(resolved_from_target, str(source.id))
