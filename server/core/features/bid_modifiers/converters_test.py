from django.test import TestCase

import core.models
from dash import constants as dash_constants
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

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.PUBLISHER, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid domain name")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.PUBLISHER, "http://example.com")
        self.assertEqual(str(ctx.exception), "Remove the following prefixes: http, https")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.PUBLISHER, "http://example.com/")
        self.assertEqual(
            str(ctx.exception), "Remove the following prefixes: http, https; Publisher should not contain /"
        )

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.PUBLISHER, "")
        self.assertEqual(str(ctx.exception), "Publisher should not be empty")

    def test_source(self):
        # full circle test
        source = magic_mixer.blend(core.models.Source, name="Outbrain", bidder_slug="b1_outbrain")

        output_value = self.converter.from_target(constants.BidModifierType.SOURCE, str(source.id))
        self.assertEqual(output_value, str(source.id))

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

        # unsupported target test
        with self.assertRaises(exceptions.BidModifierUnsupportedTarget):
            self.converter.to_target(
                constants.BidModifierType.DEVICE, dash_constants.DeviceType.get_text(dash_constants.DeviceType.UNKNOWN)
            )

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.DEVICE, 1234)

        with self.assertRaises(ValueError):
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

        # unsupported target test
        with self.assertRaises(exceptions.BidModifierUnsupportedTarget):
            self.converter.to_target(
                constants.BidModifierType.OPERATING_SYSTEM,
                dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.UNKNOWN),
            )

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

    def test_placement_medium(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.PLACEMENT, dash_constants.PlacementMedium.APP
        )
        self.assertEqual(output_value, dash_constants.PlacementMedium.get_name(dash_constants.PlacementMedium.APP))

        target_value = self.converter.to_target(constants.BidModifierType.PLACEMENT, output_value)
        self.assertEqual(target_value, dash_constants.PlacementMedium.APP)

        # unsupported target test
        with self.assertRaises(exceptions.BidModifierUnsupportedTarget):
            self.converter.to_target(
                constants.BidModifierType.PLACEMENT,
                dash_constants.PlacementMedium.get_text(dash_constants.PlacementMedium.UNKNOWN),
            )

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.PLACEMENT, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.PLACEMENT, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.PLACEMENT, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Placement Medium")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.PLACEMENT, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Placement Medium")

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

        output_value = self.converter.from_target(constants.BidModifierType.SOURCE, str(content_ad.id))
        self.assertEqual(output_value, str(content_ad.id))

        target_value = self.converter.to_target(constants.BidModifierType.AD, output_value)
        self.assertEqual(target_value, str(content_ad.id))

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.AD, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Content Ad")


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


class TestApiConverter(TestCase):
    def setUp(self):
        self.converter = converters.ApiConverter

    def test_operating_system(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.OPERATING_SYSTEM, dash_constants.OperatingSystem.MACOSX
        )
        self.assertEqual(output_value, dash_constants.OperatingSystem.get_name(dash_constants.OperatingSystem.MACOSX))

        target_value = self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, output_value)
        self.assertEqual(target_value, dash_constants.OperatingSystem.MACOSX)

        # unsupported target test
        with self.assertRaises(exceptions.BidModifierUnsupportedTarget):
            self.converter.to_target(
                constants.BidModifierType.OPERATING_SYSTEM,
                dash_constants.OperatingSystem.get_name(dash_constants.OperatingSystem.UNKNOWN),
            )

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

        # unsupported target tests
        with self.assertRaises(exceptions.BidModifierUnsupportedTarget):
            self.converter.to_target(
                constants.BidModifierType.DEVICE, dash_constants.DeviceType.get_text(dash_constants.DeviceType.UNKNOWN)
            )

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.DEVICE, 1234)

        with self.assertRaises(ValueError):
            self.converter.from_target(constants.BidModifierType.DEVICE, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.DEVICE, "invalid")
            self.assertEqual(str(ctx.exception), "Invalid Device TYpe")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.DEVICE, 1234)
            self.assertEqual(str(ctx.exception), "Invalid Device TYpe")

    def test_operating_system(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.OPERATING_SYSTEM, dash_constants.OperatingSystem.MACOSX
        )
        self.assertEqual(output_value, dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.MACOSX))

        target_value = self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, output_value)
        self.assertEqual(target_value, dash_constants.OperatingSystem.MACOSX)

        # unsupported target tests
        with self.assertRaises(exceptions.BidModifierUnsupportedTarget):
            self.converter.to_target(
                constants.BidModifierType.OPERATING_SYSTEM,
                dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.UNKNOWN),
            )

        with self.assertRaises(exceptions.BidModifierUnsupportedTarget) as ctx:
            self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, None)
        self.assertEqual(str(ctx.exception), "Unsupported Operating System Traget")

        with self.assertRaises(exceptions.BidModifierUnsupportedTarget) as ctx:
            self.converter.to_target(constants.BidModifierType.OPERATING_SYSTEM, "Other")
        self.assertEqual(str(ctx.exception), "Unsupported Operating System Traget")

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

    def test_placement_medium(self):
        # full circle test
        output_value = self.converter.from_target(
            constants.BidModifierType.PLACEMENT, dash_constants.PlacementMedium.APP
        )
        self.assertEqual(output_value, dash_constants.PlacementMedium.APP)

        target_value = self.converter.to_target(constants.BidModifierType.PLACEMENT, output_value)
        self.assertEqual(target_value, dash_constants.PlacementMedium.APP)

        # unsupported target tests
        with self.assertRaises(exceptions.BidModifierUnsupportedTarget):
            self.converter.to_target(
                constants.BidModifierType.PLACEMENT,
                dash_constants.PlacementMedium.get_text(dash_constants.PlacementMedium.UNKNOWN),
            )

        # illegal target value tests
        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.PLACEMENT, 1234)

        with self.assertRaises(KeyError):
            self.converter.from_target(constants.BidModifierType.PLACEMENT, "invalid")

        # illegal input target value tests
        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.PLACEMENT, "invalid")
        self.assertEqual(str(ctx.exception), "Invalid Placement Medium")

        with self.assertRaises(exceptions.BidModifierTargetInvalid) as ctx:
            self.converter.to_target(constants.BidModifierType.PLACEMENT, 1234)
        self.assertEqual(str(ctx.exception), "Invalid Placement Medium")

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
