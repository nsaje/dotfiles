from django.test import TestCase

import core.models
from dash import models
from utils.magic_mixer import magic_mixer

from . import constants
from . import exceptions
from . import helpers


class TestPublisherBidModifierService(TestCase):
    def test_get_source_slug(self):
        source = magic_mixer.blend(core.models.Source, bidder_slug="some_slug")

        source_slug = helpers.get_source_slug(constants.BidModifierType.PUBLISHER, source)
        self.assertEqual(source_slug, "some_slug")

        with self.assertRaises(exceptions.BidModifierSourceInvalid):
            helpers.get_source_slug(constants.BidModifierType.PUBLISHER, None)

        with self.assertRaises(exceptions.BidModifierSourceInvalid):
            helpers.get_source_slug(constants.BidModifierType.DEVICE, source_slug)

        with self.assertRaises(exceptions.BidModifierTypeInvalid):
            helpers.get_source_slug(None, None)

        with self.assertRaises(exceptions.BidModifierTypeInvalid):
            helpers.get_source_slug("", None)

    def test_check_modifier_value(self):
        helpers.check_modifier_value((helpers.MODIFIER_MAX + helpers.MODIFIER_MIN) / 2)

        with self.assertRaises(exceptions.BidModifierValueInvalid):
            helpers.check_modifier_value(None)

        with self.assertRaises(exceptions.BidModifierValueInvalid):
            helpers.check_modifier_value("")

        with self.assertRaises(exceptions.BidModifierValueInvalid):
            helpers.check_modifier_value(helpers.MODIFIER_MIN - 1)

        with self.assertRaises(exceptions.BidModifierValueInvalid):
            helpers.check_modifier_value(helpers.MODIFIER_MAX + 1)

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

        errors = []
        target = helpers.clean_bid_modifier_type_input("", errors)
        self.assertIsNone(target)
        self.assertEqual(errors, ["Invalid Bid Modifier Type"])

    def test_clean_source_bidder_slug_input(self):
        source = magic_mixer.blend(core.models.Source, bidder_slug="some_slug")

        sources_by_slug = {x.get_clean_slug(): x for x in models.Source.objects.all()}

        errors = []
        self.assertEqual(helpers.clean_source_bidder_slug_input("some_slug", sources_by_slug, errors), source)
        self.assertEqual(errors, [])

        errors = []
        self.assertEqual(helpers.clean_source_bidder_slug_input("bad slug", sources_by_slug, errors), None)
        self.assertEqual(errors, ["Invalid Source Slug"])

        errors = []
        self.assertEqual(helpers.clean_source_bidder_slug_input("", sources_by_slug, errors), None)
        self.assertEqual(errors, ["Invalid Source Slug"])

    def test_clean_bid_modifier_value_input(self):
        modifier = 1.0
        errors = []
        self.assertEqual(helpers.clean_bid_modifier_value_input(modifier, errors), None)
        self.assertEqual(errors, [])

        modifier = "ASD"
        errors = []
        self.assertEqual(helpers.clean_bid_modifier_value_input(modifier, errors), None)
        self.assertEqual(errors, ["Invalid Bid Modifier"])

        modifier = 0.0
        errors = []
        self.assertEqual(helpers.clean_bid_modifier_value_input(modifier, errors), 0.0)
        self.assertEqual(errors, [helpers._get_modifier_bounds_error_message(modifier)])
