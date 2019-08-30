import decimal

from django.test import TestCase

from core.features import bid_modifiers
from core.models.settings.ad_group_source_settings import exceptions as agss_exceptions
from dash import constants
from dash import models
from utils.magic_mixer import magic_mixer


class AdGroupSettingsChangeTestCase(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(models.AdGroup)
        self.input_bid_modifiers_list = [0.3, 1.4]

    def _add_sources_with_modifiers(self, modifiers_list, bid_value=None):

        if self.ad_group.bidding_type == constants.BiddingType.CPC:
            bid_value_attr = "cpc"
            source_bid_value_attr = "cpc_cc"
        else:
            bid_value_attr = "cpm"
            source_bid_value_attr = "cpm"

        if bid_value is None:
            bid_value = decimal.Decimal(getattr(self.ad_group.settings, bid_value_attr))

        for modifier in modifiers_list:
            ad_group_source = magic_mixer.blend(models.AdGroupSource, ad_group=self.ad_group)
            magic_mixer.blend(
                models.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.constants.BidModifierType.SOURCE,
                modifier=modifier,
                target=bid_modifiers.converters.TargetConverter._to_source_target(ad_group_source.source.id),
            )
            ad_group_source.settings.update(None, **{source_bid_value_attr: decimal.Decimal(modifier) * bid_value})

    def _assert_bid_modifiers(self, expected_bid_modifiers_list):
        output_bid_modifiers_list = list(
            models.BidModifier.objects.filter(ad_group=self.ad_group).order_by("id").values_list("modifier", flat=True)
        )
        self.assertEqual(output_bid_modifiers_list, expected_bid_modifiers_list)

    def test_without_max_cpc(self):
        self.ad_group.settings.update_unsafe(
            None, cpc_cc=None, cpc=decimal.Decimal("0.1"), max_cpm=None, cpm=decimal.Decimal("1.0")
        )

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        self.ad_group.settings.update(None, cpc=decimal.Decimal("0.2"))

        self._assert_bid_modifiers([e / 2 for e in self.input_bid_modifiers_list])

    def test_with_max_cpc(self):
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))

        self._add_sources_with_modifiers([e / 2 for e in self.input_bid_modifiers_list])

        self.ad_group.settings.update(None, cpc=decimal.Decimal("0.2"))

        self._assert_bid_modifiers([e / 4 for e in self.input_bid_modifiers_list])

    def test_with_max_cpc_over_limit(self):
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))

        with self.assertRaises(agss_exceptions.MaximalCPCTooHigh):
            self._add_sources_with_modifiers(self.input_bid_modifiers_list)

    def test_without_max_cpm(self):
        self.ad_group.settings.update_unsafe(
            None, cpc_cc=None, cpc=decimal.Decimal("0.1"), max_cpm=None, cpm=decimal.Decimal("1.0")
        )
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        self.ad_group.settings.update(None, cpm=decimal.Decimal("2.0"))

        self._assert_bid_modifiers([e / 2 for e in self.input_bid_modifiers_list])

    def test_with_max_cpm(self):
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_sources_with_modifiers([e / 2 for e in self.input_bid_modifiers_list])

        self.ad_group.settings.update(None, cpm=decimal.Decimal("2.0"))

        self._assert_bid_modifiers([e / 4 for e in self.input_bid_modifiers_list])

    def test_with_max_cpm_over_limit(self):
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        with self.assertRaises(agss_exceptions.MaximalCPMTooHigh):
            self._add_sources_with_modifiers(self.input_bid_modifiers_list)


class AdGroupSourceSettingsChangeTestCase(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(models.AdGroup)

    def _add_source_with_modifier(self, bid_modifier):
        self.ad_group_source = magic_mixer.blend(models.AdGroupSource, ad_group=self.ad_group)
        if self.ad_group.bidding_type == constants.BiddingType.CPC:
            bid_value_attr = "cpc"
            source_bid_value_attr = "cpc_cc"
        else:
            bid_value_attr = "cpm"
            source_bid_value_attr = "cpm"

        bid_value = decimal.Decimal(getattr(self.ad_group.settings, bid_value_attr))
        magic_mixer.blend(
            models.BidModifier,
            ad_group=self.ad_group,
            type=bid_modifiers.constants.BidModifierType.SOURCE,
            modifier=bid_modifier,
            target=bid_modifiers.converters.TargetConverter._to_source_target(self.ad_group_source.source.id),
        )
        self.ad_group_source.settings.update(None, **{source_bid_value_attr: decimal.Decimal(bid_modifier) * bid_value})

    def _assert_bid_modifier(self, expected_bid_modifier):
        output_bid_modifier = (
            models.BidModifier.objects.filter(
                ad_group=self.ad_group,
                target=bid_modifiers.converters.TargetConverter._to_source_target(self.ad_group_source.source.id),
            )
            .order_by("id")
            .values_list("modifier", flat=True)
            .first()
        )
        self.assertEqual(output_bid_modifier, expected_bid_modifier)

    def test_without_max_cpc_reduce(self):
        bid_modifier = 0.3
        self.ad_group.settings.update_unsafe(
            None, cpc_cc=None, cpc=decimal.Decimal("0.1"), max_cpm=None, cpm=decimal.Decimal("1.0")
        )

        self._add_source_with_modifier(bid_modifier)

        self.ad_group_source.settings.update(None, cpc_cc=decimal.Decimal("0.06"))

        self._assert_bid_modifier(2 * bid_modifier)

    def test_without_max_cpc_increase(self):
        bid_modifier = 1.4
        self.ad_group.settings.update_unsafe(
            None, cpc_cc=None, cpc=decimal.Decimal("0.1"), max_cpm=None, cpm=decimal.Decimal("1.0")
        )

        self._add_source_with_modifier(bid_modifier)

        self.ad_group_source.settings.update(None, cpc_cc=decimal.Decimal("0.28"))

        self._assert_bid_modifier(2 * bid_modifier)

    def test_with_max_cpc_reduce(self):
        bid_modifier = 0.3
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))

        self._add_source_with_modifier(bid_modifier)

        self.ad_group_source.settings.update(None, cpc_cc=decimal.Decimal("0.06"))

        self._assert_bid_modifier(2 * bid_modifier)

    def test_with_max_cpc_increase(self):
        bid_modifier = 0.7
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))

        self._add_source_with_modifier(bid_modifier)

        with self.assertRaises(agss_exceptions.MaximalCPCTooHigh):
            self.ad_group_source.settings.update(None, cpc_cc=decimal.Decimal("0.28"))

    def test_with_max_cpc_bid_modifier_over_limit(self):
        bid_modifier = 0.3
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))

        self._add_source_with_modifier(bid_modifier)

        with self.assertRaises(agss_exceptions.MaximalCPCTooHigh):
            self.ad_group_source.settings.update(None, cpc_cc=decimal.Decimal("1.2"))

    def test_without_max_cpm_reduce(self):
        bid_modifier = 0.3
        self.ad_group.settings.update_unsafe(
            None, cpc_cc=None, cpc=decimal.Decimal("0.1"), max_cpm=None, cpm=decimal.Decimal("1.0")
        )
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_source_with_modifier(bid_modifier)

        self.ad_group_source.settings.update(None, cpm=decimal.Decimal("0.6"))

        self._assert_bid_modifier(2 * bid_modifier)

    def test_without_max_cpm_increase(self):
        bid_modifier = 1.4
        self.ad_group.settings.update_unsafe(
            None, cpc_cc=None, cpc=decimal.Decimal("0.1"), max_cpm=None, cpm=decimal.Decimal("1.0")
        )
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_source_with_modifier(bid_modifier)

        self.ad_group_source.settings.update(None, cpm=decimal.Decimal("2.8"))

        self._assert_bid_modifier(2 * bid_modifier)

    def test_with_max_cpm_reduce(self):
        bid_modifier = 0.3
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_source_with_modifier(bid_modifier)

        self.ad_group_source.settings.update(None, cpm=decimal.Decimal("0.6"))

        self._assert_bid_modifier(2 * bid_modifier)

    def test_with_max_cpm_increase(self):
        bid_modifier = 0.7
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_source_with_modifier(bid_modifier)

        with self.assertRaises(agss_exceptions.MaximalCPMTooHigh):
            self.ad_group_source.settings.update(None, cpm=decimal.Decimal("1.4"))

    def test_with_max_cpm_bid_modifier_over_limit(self):
        bid_modifier = 0.3
        self.ad_group.settings.update_unsafe(None, cpc_cc=decimal.Decimal("0.1"), max_cpm=decimal.Decimal("1.0"))
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_source_with_modifier(bid_modifier)

        with self.assertRaises(agss_exceptions.MaximalCPMTooHigh):
            self.ad_group_source.settings.update(None, cpm=decimal.Decimal("12.0"))


class SwitchBiddingTypeTestCase(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(models.AdGroup)
        self.input_bid_modifiers_list = [0.3, 1.4]

    def _add_sources_with_modifiers(self, modifiers_list, cpm_factor=2):
        cpc = decimal.Decimal(self.ad_group.settings.cpc)
        cpm = decimal.Decimal(self.ad_group.settings.cpm)

        for modifier in modifiers_list:
            source_cpc = decimal.Decimal(modifier) * cpc
            source_cpm = decimal.Decimal(modifier) * cpm * decimal.Decimal(cpm_factor)

            ad_group_source = magic_mixer.blend(models.AdGroupSource, ad_group=self.ad_group)
            magic_mixer.blend(
                models.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.constants.BidModifierType.SOURCE,
                modifier=modifier,
                target=bid_modifiers.converters.TargetConverter._to_source_target(ad_group_source.source.id),
            )
            ad_group_source.settings.update_unsafe(None, cpc_cc=source_cpc, cpm=source_cpm)

    def _assert_bid_modifiers(self, expected_bid_modifiers_list):
        output_bid_modifiers_list = list(
            models.BidModifier.objects.filter(ad_group=self.ad_group).order_by("id").values_list("modifier", flat=True)
        )
        self.assertEqual(output_bid_modifiers_list, expected_bid_modifiers_list)

    def test_cpc_to_cpm(self):
        cpm_factor = 2
        self.ad_group.settings.update_unsafe(
            None, cpc_cc=None, cpc=decimal.Decimal("0.1"), max_cpm=None, cpm=decimal.Decimal("2.0")
        )

        self._add_sources_with_modifiers(self.input_bid_modifiers_list, cpm_factor=cpm_factor)

        self.ad_group.update_bidding_type(None, bidding_type=constants.BiddingType.CPM)

        self._assert_bid_modifiers([e * cpm_factor for e in self.input_bid_modifiers_list])

    def test_cpm_to_cpc(self):
        cpm_factor = 2
        self.ad_group.settings.update_unsafe(
            None, cpc_cc=None, cpc=decimal.Decimal("0.1"), max_cpm=None, cpm=decimal.Decimal("2.0")
        )
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_sources_with_modifiers(self.input_bid_modifiers_list, cpm_factor=cpm_factor)

        self.ad_group.update_bidding_type(None, bidding_type=constants.BiddingType.CPC)

        self._assert_bid_modifiers(self.input_bid_modifiers_list)
