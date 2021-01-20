import functools
import operator

from django.test import TestCase

import dash.constants
import dash.models
from utils.magic_mixer import magic_mixer

from .. import bid_modifiers


class BaseOverviewTestCase(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(dash.models.AdGroup)
        self.other_ad_group = magic_mixer.blend(dash.models.AdGroup)
        self.source_1 = magic_mixer.blend(dash.models.Source, bidder_slug="some_slug_1")
        self.source_2 = magic_mixer.blend(dash.models.Source, bidder_slug="some_slug_2")
        self.source_3 = magic_mixer.blend(dash.models.Source, bidder_slug="some_slug_3")
        self.source_4 = magic_mixer.blend(dash.models.Source, bidder_slug="some_slug_4")
        self.ad_group_source_1 = magic_mixer.blend(
            dash.models.AdGroupSource, ad_group=self.ad_group, source=self.source_1
        )
        self.ad_group_source_2 = magic_mixer.blend(
            dash.models.AdGroupSource, ad_group=self.ad_group, source=self.source_2
        )
        self.ad_group_source_3 = magic_mixer.blend(
            dash.models.AdGroupSource, ad_group=self.ad_group, source=self.source_3
        )
        self.ad_group_source_4 = magic_mixer.blend(
            dash.models.AdGroupSource, ad_group=self.ad_group, source=self.source_4
        )
        self.other_ad_group_source_1 = magic_mixer.blend(
            dash.models.AdGroupSource, ad_group=self.other_ad_group, source=self.source_1
        )
        self.ad_group_source_1.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.ad_group_source_2.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.ad_group_source_3.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.ad_group_source_4.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.other_ad_group_source_1.settings.update_unsafe(
            None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE
        )

        self.content_ad_1 = magic_mixer.blend(dash.models.ContentAd, ad_group=self.ad_group)
        self.content_ad_2 = magic_mixer.blend(dash.models.ContentAd, ad_group=self.ad_group)
        self.content_ad_3 = magic_mixer.blend(dash.models.ContentAd, ad_group=self.ad_group)
        self.other_content_ad_1 = magic_mixer.blend(dash.models.ContentAd, ad_group=self.other_ad_group)
        self.other_content_ad_2 = magic_mixer.blend(dash.models.ContentAd, ad_group=self.other_ad_group)

        self.ag_test_publisher_1, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.PUBLISHER, "test_publisher_1", self.source_1, 0.53
        )
        self.ag_test_publisher_2, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.PUBLISHER, "test_publisher_2", self.source_1, 0.11
        )
        self.ag_test_publisher_3, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.PUBLISHER, "test_publisher_3", self.source_1, 1.15
        )

        self.ag_test_source_1, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_1.id), None, 0.61
        )
        self.ag_test_source_2, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_2.id), None, 1.16
        )
        self.ag_test_source_3, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_3.id), None, 0.96
        )
        self.ag_test_source_4, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_4.id), None, 2.1
        )

        self.ag_test_device_1, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.DEVICE, str(dash.constants.DeviceType.DESKTOP), None, 0.13
        )
        self.ag_test_device_2, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.DEVICE, str(dash.constants.DeviceType.MOBILE), None, 1.32
        )

        self.ag_test_operating_system_1, _ = bid_modifiers.set(
            self.ad_group,
            bid_modifiers.BidModifierType.OPERATING_SYSTEM,
            dash.constants.OperatingSystem.ANDROID,
            None,
            0.74,
        )
        self.ag_test_operating_system_2, _ = bid_modifiers.set(
            self.ad_group,
            bid_modifiers.BidModifierType.OPERATING_SYSTEM,
            dash.constants.OperatingSystem.IOS,
            None,
            1.22,
        )
        self.ag_test_operating_system_3, _ = bid_modifiers.set(
            self.ad_group,
            bid_modifiers.BidModifierType.OPERATING_SYSTEM,
            dash.constants.OperatingSystem.WINDOWS,
            None,
            2.10,
        )
        self.ag_test_operating_system_4, _ = bid_modifiers.set(
            self.ad_group,
            bid_modifiers.BidModifierType.OPERATING_SYSTEM,
            dash.constants.OperatingSystem.MACOSX,
            None,
            0.02,
        )
        self.ag_test_operating_system_5, _ = bid_modifiers.set(
            self.ad_group,
            bid_modifiers.BidModifierType.OPERATING_SYSTEM,
            dash.constants.OperatingSystem.LINUX,
            None,
            2.01,
        )

        self.ag_test_environment_1, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.APP, None, 0.36
        )
        self.ag_test_environment_2, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 1.76
        )

        self.ag_test_country_1, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.COUNTRY, "test_country_1", None, 0.91
        )
        self.ag_test_country_2, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.COUNTRY, "test_country_2", None, 2.10
        )
        self.ag_test_country_3, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.COUNTRY, "test_country_3", None, 1.11
        )
        self.ag_test_country_4, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.COUNTRY, "test_country_4", None, 0.49
        )
        self.ag_test_country_5, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.COUNTRY, "test_country_5", None, 1.6
        )

        self.ag_test_state_1, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.STATE, "test_state_1", None, 0.73
        )

        self.ag_test_dma_1, _ = bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.DMA, "100", None, 0.26)
        self.ag_test_dma_2, _ = bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.DMA, "101", None, 1.61)

        self.ag_test_ad_1, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.AD, str(self.content_ad_1.id), None, 1.71
        )
        self.ag_test_ad_2, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.AD, str(self.content_ad_2.id), None, 0.81
        )
        self.ag_test_ad_3, _ = bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.AD, str(self.content_ad_3.id), None, 1.5
        )

        self.oag_test_publisher_1, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.PUBLISHER, "test_publisher_1", self.source_1, 10.35
        )
        self.oag_test_publisher_2, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.PUBLISHER, "test_publisher_2", self.source_1, 0.011
        )

        self.oag_test_source_1, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_1.id), None, 10.46
        )

        self.oag_test_device_1, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.DEVICE, dash.constants.DeviceType.DESKTOP, None, 10.37
        )
        self.oag_test_device_2, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.DEVICE, dash.constants.DeviceType.MOBILE, None, 0.012
        )

        self.oag_test_operating_system_1, _ = bid_modifiers.set(
            self.other_ad_group,
            bid_modifiers.BidModifierType.OPERATING_SYSTEM,
            dash.constants.OperatingSystem.ANDROID,
            None,
            10.43,
        )
        self.oag_test_operating_system_2, _ = bid_modifiers.set(
            self.other_ad_group,
            bid_modifiers.BidModifierType.OPERATING_SYSTEM,
            dash.constants.OperatingSystem.IOS,
            None,
            0.013,
        )

        self.oag_test_environment_1, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.APP, None, 10.62
        )
        self.oag_test_environment_2, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 0.014
        )

        self.oag_test_country_1, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.COUNTRY, "test_country_1", None, 10.09
        )
        self.oag_test_country_2, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.COUNTRY, "test_country_2", None, 0.014
        )

        self.oag_test_state_1, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.STATE, "test_state_1", None, 10.43
        )
        self.oag_test_state_2, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.STATE, "test_state_2", None, 0.015
        )

        self.oag_test_ad_1, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.AD, str(self.other_content_ad_1.id), None, 10.21
        )
        self.oag_test_ad_2, _ = bid_modifiers.set(
            self.other_ad_group, bid_modifiers.BidModifierType.AD, str(self.other_content_ad_2.id), None, 0.016
        )


class TestGetMinMaxFactors(BaseOverviewTestCase):
    def test_all(self):
        expected_min_factor = _multiply_modifiers(
            min,
            self.ag_test_publisher_2,
            self.ag_test_source_1,
            self.ag_test_device_1,
            self.ag_test_operating_system_4,
            self.ag_test_environment_1,
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
            self.ag_test_environment_2,
            self.ag_test_country_2,
            self.ag_test_state_1,
            self.ag_test_dma_2,
            self.ag_test_ad_1,
        )

        min_factor, max_factor = bid_modifiers.get_min_max_factors(self.ad_group.id)

        self.assertAlmostEqual(min_factor, expected_min_factor, places=13)
        self.assertAlmostEqual(max_factor, expected_max_factor, places=13)

    def test_included_types(self):
        expected_min_factor = _multiply_modifiers(
            min, self.ag_test_source_1, self.ag_test_operating_system_4, self.ag_test_country_4
        )
        expected_max_factor = _multiply_modifiers(
            max, self.ag_test_source_4, self.ag_test_operating_system_3, self.ag_test_country_2
        )

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id,
            included_types=[
                bid_modifiers.BidModifierType.SOURCE,
                bid_modifiers.BidModifierType.OPERATING_SYSTEM,
                bid_modifiers.BidModifierType.COUNTRY,
            ],
        )

        self.assertAlmostEqual(min_factor, expected_min_factor, places=13)
        self.assertAlmostEqual(max_factor, expected_max_factor, places=13)

    def test_excluded_types(self):
        expected_min_factor = _multiply_modifiers(
            min,
            self.ag_test_publisher_2,
            self.ag_test_device_1,
            self.ag_test_environment_1,
            self.ag_test_state_1,
            self.ag_test_dma_1,
            self.ag_test_ad_2,
        )
        expected_max_factor = _multiply_modifiers(
            max,
            self.ag_test_publisher_3,
            self.ag_test_device_2,
            self.ag_test_environment_2,
            self.ag_test_state_1,
            self.ag_test_dma_2,
            self.ag_test_ad_1,
        )

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id,
            excluded_types=[
                bid_modifiers.BidModifierType.SOURCE,
                bid_modifiers.BidModifierType.OPERATING_SYSTEM,
                bid_modifiers.BidModifierType.COUNTRY,
            ],
        )

        self.assertAlmostEqual(min_factor, expected_min_factor, places=13)
        self.assertAlmostEqual(max_factor, expected_max_factor, places=13)

    def test_included_types_empty(self):
        min_factor, max_factor = bid_modifiers.get_min_max_factors(self.ad_group.id, included_types=[])

        self.assertAlmostEqual(min_factor, 1, places=13)
        self.assertAlmostEqual(max_factor, 1, places=13)

    def test_excluded_types_empty(self):
        expected_min_factor = _multiply_modifiers(
            min,
            self.ag_test_publisher_2,
            self.ag_test_source_1,
            self.ag_test_device_1,
            self.ag_test_operating_system_4,
            self.ag_test_environment_1,
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
            self.ag_test_environment_2,
            self.ag_test_country_2,
            self.ag_test_state_1,
            self.ag_test_dma_2,
            self.ag_test_ad_1,
        )

        min_factor, max_factor = bid_modifiers.get_min_max_factors(self.ad_group.id, excluded_types=[])

        self.assertAlmostEqual(min_factor, expected_min_factor, places=13)
        self.assertAlmostEqual(max_factor, expected_max_factor, places=13)

    def test_included_types_non_existing(self):
        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.other_ad_group.id, included_types=[bid_modifiers.BidModifierType.DMA]
        )

        self.assertAlmostEqual(min_factor, 1, places=13)
        self.assertAlmostEqual(max_factor, 1, places=13)


class TestGetMinMaxFactorsDetailed(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(dash.models.AdGroup)
        self.source_1 = magic_mixer.blend(dash.models.Source, bidder_slug="some_slug_1")
        self.source_2 = magic_mixer.blend(dash.models.Source, bidder_slug="some_slug_2")
        self.ad_group_source_1 = magic_mixer.blend(
            dash.models.AdGroupSource, ad_group=self.ad_group, source=self.source_1
        )
        self.ad_group_source_2 = magic_mixer.blend(
            dash.models.AdGroupSource, ad_group=self.ad_group, source=self.source_2
        )
        self.ad_group_source_1.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.ad_group_source_2.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.content_ad_1 = magic_mixer.blend(dash.models.ContentAd, ad_group=self.ad_group)
        self.content_ad_2 = magic_mixer.blend(dash.models.ContentAd, ad_group=self.ad_group)

    def test_source_all_higher(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_1.id), None, 1.1)
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_2.id), None, 1.2)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.SOURCE]
        )
        self.assertEqual(min_factor, 1.1)
        self.assertEqual(max_factor, 1.2)

    def test_source_all_lower(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_1.id), None, 0.9)
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_2.id), None, 0.8)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.SOURCE]
        )
        self.assertEqual(min_factor, 0.8)
        self.assertEqual(max_factor, 0.9)

    def test_source_not_all_higher(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_1.id), None, 1.1)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.SOURCE]
        )
        self.assertEqual(min_factor, 1.0)
        self.assertEqual(max_factor, 1.1)

    def test_source_not_all_lower(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_1.id), None, 0.9)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.SOURCE]
        )
        self.assertEqual(min_factor, 0.9)
        self.assertEqual(max_factor, 1.0)

    def test_source_modifier_for_inactive_source(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_1.id), None, 1.1)
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_2.id), None, 1.2)
        self.ad_group_source_2.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.INACTIVE)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.SOURCE]
        )
        self.assertEqual(min_factor, 1.1)
        self.assertEqual(max_factor, 1.1)

    def test_source_no_modifier_for_active_source(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source_1.id), None, 1.1)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.SOURCE]
        )
        self.assertEqual(min_factor, 1.0)
        self.assertEqual(max_factor, 1.1)

    def test_ad_all_higher(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.AD, str(self.content_ad_1.id), None, 1.1)
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.AD, str(self.content_ad_2.id), None, 1.2)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.AD]
        )
        self.assertEqual(min_factor, 1.1)
        self.assertEqual(max_factor, 1.2)

    def test_ad_not_all_lower(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.AD, str(self.content_ad_1.id), None, 0.9)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.AD]
        )
        self.assertEqual(min_factor, 0.9)
        self.assertEqual(max_factor, 1.0)

    def test_ad_modifier_for_inactive_source(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.AD, str(self.content_ad_1.id), None, 1.1)
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.AD, str(self.content_ad_2.id), None, 1.2)
        self.content_ad_2.update(None, state=dash.constants.ContentAdSourceState.INACTIVE)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.AD]
        )
        self.assertEqual(min_factor, 1.1)
        self.assertEqual(max_factor, 1.1)

    def test_ad_no_modifier_for_active_source(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.AD, str(self.content_ad_1.id), None, 1.1)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.AD]
        )
        self.assertEqual(min_factor, 1.0)
        self.assertEqual(max_factor, 1.1)

    def test_environment_all_higher(self):
        bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.APP, None, 1.1
        )
        bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 1.2
        )

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.ENVIRONMENT]
        )
        self.assertEqual(min_factor, 1.1)
        self.assertEqual(max_factor, 1.2)

    def test_environment_all_lower(self):
        bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.APP, None, 0.9
        )
        bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.SITE, None, 0.8
        )

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.ENVIRONMENT]
        )
        self.assertEqual(min_factor, 0.8)
        self.assertEqual(max_factor, 0.9)

    def test_environment_not_all_higher(self):
        bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.APP, None, 1.1
        )

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.ENVIRONMENT]
        )
        self.assertEqual(min_factor, 1.0)
        self.assertEqual(max_factor, 1.1)

    def test_environment_not_all_lower(self):
        bid_modifiers.set(
            self.ad_group, bid_modifiers.BidModifierType.ENVIRONMENT, dash.constants.Environment.APP, None, 0.9
        )

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.ENVIRONMENT]
        )
        self.assertEqual(min_factor, 0.9)
        self.assertEqual(max_factor, 1.0)

    def test_country_not_all_higher(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.COUNTRY, "us", None, 1.1)
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.COUNTRY, "uk", None, 1.2)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.COUNTRY]
        )
        self.assertEqual(min_factor, 1.0)
        self.assertEqual(max_factor, 1.2)

    def test_country_not_all_lower(self):
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.COUNTRY, "us", None, 0.9)
        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.COUNTRY, "uk", None, 0.8)

        min_factor, max_factor = bid_modifiers.get_min_max_factors(
            self.ad_group.id, included_types=[bid_modifiers.BidModifierType.COUNTRY]
        )
        self.assertEqual(min_factor, 0.8)
        self.assertEqual(max_factor, 1.0)


def _multiply_modifiers(min_max_fn, *bid_modifiers):
    return functools.reduce(operator.mul, [min_max_fn(e.modifier, 1.) for e in bid_modifiers], 1.)


class TestGetTypeSummaries(BaseOverviewTestCase):
    def test_all(self):
        self.assertEqual(
            bid_modifiers.get_type_summaries(self.ad_group.id),
            [
                bid_modifiers.BidModifierTypeSummary(
                    count=3, max=1.15, min=0.11, type=bid_modifiers.BidModifierType.PUBLISHER
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=4, max=2.1, min=0.61, type=bid_modifiers.BidModifierType.SOURCE
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=2, max=1.32, min=0.13, type=bid_modifiers.BidModifierType.DEVICE
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=5, max=2.1, min=0.02, type=bid_modifiers.BidModifierType.OPERATING_SYSTEM
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=2, max=1.76, min=0.36, type=bid_modifiers.BidModifierType.ENVIRONMENT
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=5, max=2.1, min=0.49, type=bid_modifiers.BidModifierType.COUNTRY
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=1, max=1.0, min=0.73, type=bid_modifiers.BidModifierType.STATE
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=2, max=1.61, min=0.26, type=bid_modifiers.BidModifierType.DMA
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=3, max=1.71, min=0.81, type=bid_modifiers.BidModifierType.AD
                ),
            ],
        )

    def test_include(self):
        self.assertEqual(
            bid_modifiers.get_type_summaries(
                self.ad_group.id,
                included_types=[
                    bid_modifiers.BidModifierType.SOURCE,
                    bid_modifiers.BidModifierType.OPERATING_SYSTEM,
                    bid_modifiers.BidModifierType.COUNTRY,
                ],
            ),
            [
                bid_modifiers.BidModifierTypeSummary(
                    count=4, max=2.1, min=0.61, type=bid_modifiers.BidModifierType.SOURCE
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=5, max=2.1, min=0.02, type=bid_modifiers.BidModifierType.OPERATING_SYSTEM
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=5, max=2.1, min=0.49, type=bid_modifiers.BidModifierType.COUNTRY
                ),
            ],
        )

    def test_exclude(self):
        self.assertEqual(
            bid_modifiers.get_type_summaries(
                self.ad_group.id,
                excluded_types=[
                    bid_modifiers.BidModifierType.SOURCE,
                    bid_modifiers.BidModifierType.OPERATING_SYSTEM,
                    bid_modifiers.BidModifierType.COUNTRY,
                ],
            ),
            [
                bid_modifiers.BidModifierTypeSummary(
                    count=3, max=1.15, min=0.11, type=bid_modifiers.BidModifierType.PUBLISHER
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=2, max=1.32, min=0.13, type=bid_modifiers.BidModifierType.DEVICE
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=2, max=1.76, min=0.36, type=bid_modifiers.BidModifierType.ENVIRONMENT
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=1, max=1.0, min=0.73, type=bid_modifiers.BidModifierType.STATE
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=2, max=1.61, min=0.26, type=bid_modifiers.BidModifierType.DMA
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=3, max=1.71, min=0.81, type=bid_modifiers.BidModifierType.AD
                ),
            ],
        )

    def test_include_exclude(self):
        self.assertEqual(
            bid_modifiers.get_type_summaries(
                self.ad_group.id,
                included_types=[
                    bid_modifiers.BidModifierType.SOURCE,
                    bid_modifiers.BidModifierType.OPERATING_SYSTEM,
                    bid_modifiers.BidModifierType.COUNTRY,
                ],
                excluded_types=[bid_modifiers.BidModifierType.OPERATING_SYSTEM],
            ),
            [
                bid_modifiers.BidModifierTypeSummary(
                    count=4, max=2.1, min=0.61, type=bid_modifiers.BidModifierType.SOURCE
                ),
                bid_modifiers.BidModifierTypeSummary(
                    count=5, max=2.1, min=0.49, type=bid_modifiers.BidModifierType.COUNTRY
                ),
            ],
        )
