import functools
import operator

from django.test import TestCase

from dash import constants as dash_constants
from dash import models as dash_models
from utils.magic_mixer import magic_mixer

from . import constants
from . import overview
from . import service


class TestGetMinMaxFactors(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(dash_models.AdGroup)
        self.other_ad_group = magic_mixer.blend(dash_models.AdGroup)
        self.source_1 = magic_mixer.blend(dash_models.Source, bidder_slug="some_slug_1")
        self.source_2 = magic_mixer.blend(dash_models.Source, bidder_slug="some_slug_2")
        self.source_3 = magic_mixer.blend(dash_models.Source, bidder_slug="some_slug_3")
        self.source_4 = magic_mixer.blend(dash_models.Source, bidder_slug="some_slug_4")

        self.ag_test_publisher_1, _ = service.set(
            self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher_1", self.source_1, 0.53
        )
        self.ag_test_publisher_2, _ = service.set(
            self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher_2", self.source_1, 0.11
        )
        self.ag_test_publisher_3, _ = service.set(
            self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher_3", self.source_1, 1.15
        )

        self.ag_test_source_1, _ = service.set(
            self.ad_group, constants.BidModifierType.SOURCE, str(self.source_1.id), None, 0.61
        )
        self.ag_test_source_2, _ = service.set(
            self.ad_group, constants.BidModifierType.SOURCE, str(self.source_2.id), None, 1.16
        )
        self.ag_test_source_3, _ = service.set(
            self.ad_group, constants.BidModifierType.SOURCE, str(self.source_3.id), None, 0.96
        )
        self.ag_test_source_4, _ = service.set(
            self.ad_group, constants.BidModifierType.SOURCE, str(self.source_4.id), None, 2.1
        )

        self.ag_test_device_1, _ = service.set(
            self.ad_group, constants.BidModifierType.DEVICE, str(dash_constants.DeviceType.DESKTOP), None, 0.13
        )
        self.ag_test_device_2, _ = service.set(
            self.ad_group, constants.BidModifierType.DEVICE, str(dash_constants.DeviceType.MOBILE), None, 1.32
        )

        self.ag_test_operating_system_1, _ = service.set(
            self.ad_group,
            constants.BidModifierType.OPERATING_SYSTEM,
            dash_constants.OperatingSystem.ANDROID,
            None,
            0.74,
        )
        self.ag_test_operating_system_2, _ = service.set(
            self.ad_group, constants.BidModifierType.OPERATING_SYSTEM, dash_constants.OperatingSystem.IOS, None, 1.22
        )
        self.ag_test_operating_system_3, _ = service.set(
            self.ad_group,
            constants.BidModifierType.OPERATING_SYSTEM,
            dash_constants.OperatingSystem.WINDOWS,
            None,
            2.10,
        )
        self.ag_test_operating_system_4, _ = service.set(
            self.ad_group, constants.BidModifierType.OPERATING_SYSTEM, dash_constants.OperatingSystem.MACOSX, None, 0.02
        )
        self.ag_test_operating_system_5, _ = service.set(
            self.ad_group, constants.BidModifierType.OPERATING_SYSTEM, dash_constants.OperatingSystem.LINUX, None, 2.01
        )

        self.ag_test_placement_1, _ = service.set(
            self.ad_group, constants.BidModifierType.PLACEMENT, dash_constants.PlacementMedium.APP, None, 0.36
        )
        self.ag_test_placement_2, _ = service.set(
            self.ad_group, constants.BidModifierType.PLACEMENT, dash_constants.PlacementMedium.SITE, None, 1.76
        )

        self.ag_test_country_1, _ = service.set(
            self.ad_group, constants.BidModifierType.COUNTRY, "test_country_1", None, 0.91
        )
        self.ag_test_country_2, _ = service.set(
            self.ad_group, constants.BidModifierType.COUNTRY, "test_country_2", None, 2.10
        )
        self.ag_test_country_3, _ = service.set(
            self.ad_group, constants.BidModifierType.COUNTRY, "test_country_3", None, 1.11
        )
        self.ag_test_country_4, _ = service.set(
            self.ad_group, constants.BidModifierType.COUNTRY, "test_country_4", None, 0.49
        )
        self.ag_test_country_5, _ = service.set(
            self.ad_group, constants.BidModifierType.COUNTRY, "test_country_5", None, 1.6
        )

        self.ag_test_state_1, _ = service.set(
            self.ad_group, constants.BidModifierType.STATE, "test_state_1", None, 0.73
        )

        self.ag_test_dma_1, _ = service.set(self.ad_group, constants.BidModifierType.DMA, "100", None, 0.26)
        self.ag_test_dma_2, _ = service.set(self.ad_group, constants.BidModifierType.DMA, "101", None, 1.61)

        self.ag_test_ad_1, _ = service.set(self.ad_group, constants.BidModifierType.AD, "test_ad_1", None, 1.71)
        self.ag_test_ad_2, _ = service.set(self.ad_group, constants.BidModifierType.AD, "test_ad_2", None, 0.81)
        self.ag_test_ad_3, _ = service.set(self.ad_group, constants.BidModifierType.AD, "test_ad_3", None, 1.5)

        self.oag_test_publisher_1, _ = service.set(
            self.other_ad_group, constants.BidModifierType.PUBLISHER, "test_publisher_1", self.source_1, 10.35
        )
        self.oag_test_publisher_2, _ = service.set(
            self.other_ad_group, constants.BidModifierType.PUBLISHER, "test_publisher_2", self.source_1, 0.011
        )

        self.oag_test_source_1, _ = service.set(
            self.other_ad_group, constants.BidModifierType.SOURCE, str(self.source_1.id), None, 10.46
        )

        self.oag_test_device_1, _ = service.set(
            self.other_ad_group, constants.BidModifierType.DEVICE, dash_constants.DeviceType.DESKTOP, None, 10.37
        )
        self.oag_test_device_2, _ = service.set(
            self.other_ad_group, constants.BidModifierType.DEVICE, dash_constants.DeviceType.MOBILE, None, 0.012
        )

        self.oag_test_operating_system_1, _ = service.set(
            self.other_ad_group,
            constants.BidModifierType.OPERATING_SYSTEM,
            dash_constants.OperatingSystem.ANDROID,
            None,
            10.43,
        )
        self.oag_test_operating_system_2, _ = service.set(
            self.other_ad_group,
            constants.BidModifierType.OPERATING_SYSTEM,
            dash_constants.OperatingSystem.IOS,
            None,
            0.013,
        )

        self.oag_test_placement_1, _ = service.set(
            self.other_ad_group, constants.BidModifierType.PLACEMENT, dash_constants.PlacementMedium.APP, None, 10.62
        )
        self.oag_test_placement_2, _ = service.set(
            self.other_ad_group, constants.BidModifierType.PLACEMENT, dash_constants.PlacementMedium.SITE, None, 0.014
        )

        self.oag_test_country_1, _ = service.set(
            self.other_ad_group, constants.BidModifierType.COUNTRY, "test_country_1", None, 10.09
        )
        self.oag_test_country_2, _ = service.set(
            self.other_ad_group, constants.BidModifierType.COUNTRY, "test_country_2", None, 0.014
        )

        self.oag_test_state_1, _ = service.set(
            self.other_ad_group, constants.BidModifierType.STATE, "test_state_1", None, 10.43
        )
        self.oag_test_state_2, _ = service.set(
            self.other_ad_group, constants.BidModifierType.STATE, "test_state_2", None, 0.015
        )

        self.oag_test_ad_1, _ = service.set(self.other_ad_group, constants.BidModifierType.AD, "test_ad_1", None, 10.21)
        self.oag_test_ad_2, _ = service.set(self.other_ad_group, constants.BidModifierType.AD, "test_ad_2", None, 0.016)

    def test_all(self):
        expected_min_factor = _multiply_modifiers(
            min,
            self.ag_test_publisher_2,
            self.ag_test_source_1,
            self.ag_test_device_1,
            self.ag_test_operating_system_4,
            self.ag_test_placement_1,
            self.ag_test_country_4,
            self.ag_test_state_1,
            self.ag_test_dma_1,
            self.ag_test_ad_2,
        )
        expected_max_factor = _multiply_modifiers(
            max,
            self.ag_test_publisher_3,
            self.ag_test_source_4,
            self.ag_test_device_2,
            self.ag_test_operating_system_3,
            self.ag_test_placement_2,
            self.ag_test_country_2,
            self.ag_test_state_1,
            self.ag_test_dma_2,
            self.ag_test_ad_1,
        )

        min_factor, max_factor = overview.get_min_max_factors(self.ad_group.id)

        self.assertAlmostEqual(min_factor, expected_min_factor, places=13)
        self.assertAlmostEqual(max_factor, expected_max_factor, places=13)

    def test_included_types(self):
        expected_min_factor = _multiply_modifiers(
            min, self.ag_test_source_1, self.ag_test_operating_system_4, self.ag_test_country_4
        )
        expected_max_factor = _multiply_modifiers(
            max, self.ag_test_source_4, self.ag_test_operating_system_3, self.ag_test_country_2
        )

        min_factor, max_factor = overview.get_min_max_factors(
            self.ad_group.id,
            included_types=[
                constants.BidModifierType.SOURCE,
                constants.BidModifierType.OPERATING_SYSTEM,
                constants.BidModifierType.COUNTRY,
            ],
        )

        self.assertAlmostEqual(min_factor, expected_min_factor, places=13)
        self.assertAlmostEqual(max_factor, expected_max_factor, places=13)

    def test_excluded_types(self):
        expected_min_factor = _multiply_modifiers(
            min,
            self.ag_test_publisher_2,
            self.ag_test_device_1,
            self.ag_test_placement_1,
            self.ag_test_state_1,
            self.ag_test_dma_1,
            self.ag_test_ad_2,
        )
        expected_max_factor = _multiply_modifiers(
            max,
            self.ag_test_publisher_3,
            self.ag_test_device_2,
            self.ag_test_placement_2,
            self.ag_test_state_1,
            self.ag_test_dma_2,
            self.ag_test_ad_1,
        )

        min_factor, max_factor = overview.get_min_max_factors(
            self.ad_group.id,
            excluded_types=[
                constants.BidModifierType.SOURCE,
                constants.BidModifierType.OPERATING_SYSTEM,
                constants.BidModifierType.COUNTRY,
            ],
        )

        self.assertAlmostEqual(min_factor, expected_min_factor, places=13)
        self.assertAlmostEqual(max_factor, expected_max_factor, places=13)

    def test_included_types_empty(self):
        min_factor, max_factor = overview.get_min_max_factors(self.ad_group.id, included_types=[])

        self.assertAlmostEqual(min_factor, 1, places=13)
        self.assertAlmostEqual(max_factor, 1, places=13)

    def test_excluded_types_empty(self):
        expected_min_factor = _multiply_modifiers(
            min,
            self.ag_test_publisher_2,
            self.ag_test_source_1,
            self.ag_test_device_1,
            self.ag_test_operating_system_4,
            self.ag_test_placement_1,
            self.ag_test_country_4,
            self.ag_test_state_1,
            self.ag_test_dma_1,
            self.ag_test_ad_2,
        )
        expected_max_factor = _multiply_modifiers(
            max,
            self.ag_test_publisher_3,
            self.ag_test_source_4,
            self.ag_test_device_2,
            self.ag_test_operating_system_3,
            self.ag_test_placement_2,
            self.ag_test_country_2,
            self.ag_test_state_1,
            self.ag_test_dma_2,
            self.ag_test_ad_1,
        )

        min_factor, max_factor = overview.get_min_max_factors(self.ad_group.id, excluded_types=[])

        self.assertAlmostEqual(min_factor, expected_min_factor, places=13)
        self.assertAlmostEqual(max_factor, expected_max_factor, places=13)

    def test_included_types_non_existing(self):
        min_factor, max_factor = overview.get_min_max_factors(
            self.other_ad_group.id, included_types=[constants.BidModifierType.DMA]
        )

        self.assertAlmostEqual(min_factor, 1, places=13)
        self.assertAlmostEqual(max_factor, 1, places=13)


def _multiply_modifiers(min_max_fn, *bid_modifiers):
    return functools.reduce(operator.mul, [min_max_fn(e.modifier, 1.) for e in bid_modifiers], 1.)
