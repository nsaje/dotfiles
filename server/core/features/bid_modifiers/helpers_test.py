from django.test import TestCase

import core.models
from dash import constants as dash_constants
from dash import models
from dash.features import geolocation
from utils.magic_mixer import magic_mixer

from . import constants
from . import helpers


class TestPublisherBidModifierService(TestCase):
    def test_clean_bid_modifier_type_input(self):
        errors = []
        target = helpers.clean_bid_modifier_type_input(
            helpers.output_modifier_type(constants.BidModifierType.DEVICE), errors
        )
        self.assertEqual(target, constants.BidModifierType.DEVICE)
        self.assertEqual(errors, [])

        errors = []
        target = helpers.clean_bid_modifier_type_input("Illegal", errors)
        self.assertIsNone(target)
        self.assertEqual(errors, ["Invalid Bid Modifier Type"])

    def test_clean_source_bidder_slug_input(self):
        source = magic_mixer.blend(core.models.Source, bidder_slug="some_slug")

        sources_by_slug = {x.get_clean_slug(): x for x in models.Source.objects.all()}
        errors = []
        self.assertEqual(helpers.clean_source_bidder_slug_input("bad slug", sources_by_slug, errors), None)
        self.assertEqual(errors, ["Invalid Source Slug"])

        errors = []
        self.assertEqual(helpers.clean_source_bidder_slug_input("some_slug", sources_by_slug, errors), source)
        self.assertEqual(errors, [])

    def test_clean_bid_modifier_value_input(self):
        modifier = "ASD"
        errors = []
        self.assertEqual(helpers.clean_bid_modifier_value_input(modifier, errors), None)
        self.assertEqual(errors, ["Invalid Bid Modifier"])

        modifier = 0.0
        errors = []
        self.assertEqual(helpers.clean_bid_modifier_value_input(modifier, errors), 0.0)
        self.assertEqual(errors, ["Bid modifier too low (< 0.01)"])

        modifier = 1.0
        errors = []
        self.assertEqual(helpers.clean_bid_modifier_value_input(modifier, errors), None)
        self.assertEqual(errors, [])

    def test_clean_publisher_input(self):
        publisher = "http://example.com"
        errors = []
        self.assertEqual(helpers.clean_publisher_input(publisher, errors), "example.com")
        self.assertEqual(errors, ["Remove the following prefixes: http, https"])

        publisher = "https://example.com/"
        errors = []
        self.assertEqual(helpers.clean_publisher_input(publisher, errors), "example.com")
        self.assertEqual(errors, ["Remove the following prefixes: http, https", "Publisher should not contain /"])

    def test_clean_source_input(self):
        source = magic_mixer.blend(core.models.Source, name="Outbrain", bidder_slug="b1_outbrain")

        errors = []
        target = helpers.clean_source_input("b1_outbrain", errors)
        self.assertEqual(target, str(source.id))
        self.assertEqual(errors, [])

        errors = []
        target = helpers.clean_source_input("Illegal", errors)
        self.assertIsNone(target)
        self.assertEqual(errors, ["Invalid Source"])

    def test_output_source_target(self):
        source = magic_mixer.blend(core.models.Source, name="Outbrain", bidder_slug="b1_outbrain")

        output = helpers.output_source_target(str(source.id))
        self.assertEqual(output, "b1_outbrain")

        with self.assertRaises(ValueError):
            helpers.output_source_target("invalid")

    def test_clean_device_type_input(self):
        errors = []
        target = helpers.clean_device_type_input(
            dash_constants.DeviceType.get_text(dash_constants.DeviceType.MOBILE), errors
        )
        self.assertEqual(target, str(dash_constants.DeviceType.MOBILE))
        self.assertEqual(errors, [])

        errors = []
        target = helpers.clean_device_type_input("Illegal", errors)
        self.assertIsNone(target)
        self.assertEqual(errors, ["Invalid Device"])

    def test_output_device_type_target(self):
        output = helpers.output_device_type_target(str(dash_constants.DeviceType.MOBILE))
        self.assertEqual(output, dash_constants.DeviceType.get_text(dash_constants.DeviceType.MOBILE))

        with self.assertRaises(ValueError):
            helpers.output_device_type_target("invalid")

    def test_clean_operating_system_input(self):
        errors = []
        target = helpers.clean_operating_system_input(
            dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.ANDROID), errors
        )
        self.assertEqual(target, str(dash_constants.OperatingSystem.ANDROID))
        self.assertEqual(errors, [])

        errors = []
        target = helpers.clean_operating_system_input("Illegal", errors)
        self.assertIsNone(target)
        self.assertEqual(errors, ["Invalid Operating System"])

    def test_output_operating_system_target(self):
        output = helpers.output_operating_system_target(dash_constants.OperatingSystem.ANDROID)
        self.assertEqual(output, dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.ANDROID))

        with self.assertRaises(ValueError):
            helpers.output_operating_system_target("invalid")

    def test_clean_placement_medium_input(self):
        errors = []
        target = helpers.clean_placement_medium_input(
            dash_constants.PlacementMedium.get_text(dash_constants.PlacementMedium.SITE), errors
        )
        self.assertEqual(target, str(dash_constants.PlacementMedium.SITE))
        self.assertEqual(errors, [])

        errors = []
        target = helpers.clean_placement_medium_input(
            dash_constants.PlacementMedium.get_text(dash_constants.PlacementMedium.UNKNOWN), errors
        )
        self.assertIsNone(target)
        self.assertEqual(errors, ["Invalid Placement"])

        errors = []
        target = helpers.clean_placement_medium_input("Illegal", errors)
        self.assertIsNone(target)
        self.assertEqual(errors, ["Invalid Placement"])

    def test_output_placement_medium_target(self):
        output = helpers.output_placement_medium_target(dash_constants.PlacementMedium.SITE)
        self.assertEqual(output, dash_constants.PlacementMedium.get_text(dash_constants.PlacementMedium.SITE))

        with self.assertRaises(ValueError):
            helpers.output_placement_medium_target("invalid")

    def test_clean_geolocation_input(self):
        magic_mixer.blend(
            geolocation.Geolocation, key="US", type=dash_constants.LocationType.COUNTRY, name="United States"
        )
        magic_mixer.blend(
            geolocation.Geolocation, key="US-TX", type=dash_constants.LocationType.REGION, name="Texas, United States"
        )
        magic_mixer.blend(
            geolocation.Geolocation, key="765", type=dash_constants.LocationType.DMA, name="765 El Paso, TX"
        )

        errors = []
        target = helpers.clean_geolocation_input("US", constants.BidModifierType.COUNTRY, errors)
        self.assertEqual(target, "US")
        self.assertEqual(errors, [])

        errors = []
        target = helpers.clean_geolocation_input("US-TX", constants.BidModifierType.STATE, errors)
        self.assertEqual(target, "US-TX")
        self.assertEqual(errors, [])

        errors = []
        target = helpers.clean_geolocation_input("765", constants.BidModifierType.DMA, errors)
        self.assertEqual(target, "765")
        self.assertEqual(errors, [])

        errors = []
        target = helpers.clean_geolocation_input("Illegal", constants.BidModifierType.STATE, errors)
        self.assertIsNone(target)
        self.assertEqual(errors, ["Invalid Geolocation"])

        errors = []
        target = helpers.clean_geolocation_input("US", constants.BidModifierType.DMA, errors)
        self.assertIsNone(target)
        self.assertEqual(errors, ["Invalid Geolocation"])
