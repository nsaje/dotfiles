import decimal
from datetime import timedelta

from django.test import TestCase

from core.features import bid_modifiers
from core.features.multicurrency.service.update import _recalculate_ad_group_amounts
from core.models.settings.ad_group_source_settings import exceptions as agss_exceptions
from dash import constants
from dash import models
from utils import dates_helper
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


class MulticurrencyUpdateTestCase(TestCase):
    def test_recalculate_ad_group_amounts(self):
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today() - timedelta(days=1),
            exchange_rate=decimal.Decimal("0.8968"),
        )

        ad_group = magic_mixer.blend(
            models.AdGroup, bidding_type=constants.BiddingType.CPC, campaign__account__currency=constants.Currency.EUR
        )

        ad_group.settings.update_unsafe(
            None,
            cpc_cc=None,
            local_cpc_cc=None,
            max_cpm=None,
            local_max_cpm=None,
            cpc=decimal.Decimal("20.0000"),
            local_cpc=decimal.Decimal("17.9360"),
            cpm=decimal.Decimal("25.0000"),
            local_cpm=decimal.Decimal("22.4200"),
            b1_sources_group_cpc_cc=decimal.Decimal("0.2230"),
            local_b1_sources_group_cpc_cc=decimal.Decimal("0.2000"),
            b1_sources_group_cpm=decimal.Decimal("0.0096"),
            local_b1_sources_group_cpm=decimal.Decimal("0.0086"),
            b1_sources_group_enabled=True,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        )

        ad_group_source_1 = magic_mixer.blend(models.AdGroupSource, ad_group=ad_group)
        ad_group_source_2 = magic_mixer.blend(
            models.AdGroupSource, ad_group=ad_group, source__source_type__type=constants.SourceType.B1
        )

        ad_group_source_1.settings.update_unsafe(
            None,
            cpc_cc=decimal.Decimal("0.2230"),
            local_cpc_cc=decimal.Decimal("0.2000"),
            cpm=decimal.Decimal("0.9852"),
            local_cpm=decimal.Decimal("0.8835"),
        )
        ad_group_source_2.settings.update_unsafe(
            None,
            cpc_cc=decimal.Decimal("0.2230"),
            local_cpc_cc=decimal.Decimal("0.2000"),
            cpm=decimal.Decimal("0.9852"),
            local_cpm=decimal.Decimal("0.8835"),
        )

        self.assertEqual(ad_group.settings.cpc, decimal.Decimal("20.0000"))
        self.assertEqual(ad_group.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group.settings.b1_sources_group_cpc_cc, decimal.Decimal("0.2230"))
        self.assertEqual(ad_group.settings.local_b1_sources_group_cpc_cc, decimal.Decimal("0.2000"))

        self.assertEqual(ad_group_source_1.settings.cpc_cc, decimal.Decimal("0.2230"))
        self.assertEqual(ad_group_source_1.settings.local_cpc_cc, decimal.Decimal("0.2000"))
        self.assertEqual(ad_group_source_2.settings.cpc_cc, decimal.Decimal("0.2230"))
        self.assertEqual(ad_group_source_2.settings.local_cpc_cc, decimal.Decimal("0.2000"))

        self.assertAlmostEqual(
            ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source_1.source.id)
            ).modifier,
            float(decimal.Decimal("0.2230") / decimal.Decimal("20.0000")),
            places=8,
        )
        self.assertAlmostEqual(
            ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source_2.source.id)
            ).modifier,
            float(decimal.Decimal("0.2230") / decimal.Decimal("20.0000")),
            places=8,
        )

        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today(),
            exchange_rate=decimal.Decimal("0.9061"),
        )

        # artificially create the condition that caused multicurrency update failure
        ad_group_source_2.settings.update_unsafe(
            None, cpc_cc=decimal.Decimal("0.2207"), local_cpc_cc=decimal.Decimal("0.2000")
        )

        _recalculate_ad_group_amounts(ad_group.campaign)

        ad_group.refresh_from_db()
        ad_group_source_1.refresh_from_db()
        ad_group_source_2.refresh_from_db()

        self.assertEqual(ad_group.settings.cpc, decimal.Decimal("19.7947"))
        self.assertEqual(ad_group.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group.settings.b1_sources_group_cpc_cc, decimal.Decimal("0.2207"))
        self.assertEqual(ad_group.settings.local_b1_sources_group_cpc_cc, decimal.Decimal("0.2000"))

        self.assertEqual(ad_group_source_1.settings.cpc_cc, decimal.Decimal("0.2207"))
        self.assertEqual(ad_group_source_1.settings.local_cpc_cc, decimal.Decimal("0.2000"))
        self.assertEqual(ad_group_source_2.settings.cpc_cc, decimal.Decimal("0.2207"))
        self.assertEqual(ad_group_source_2.settings.local_cpc_cc, decimal.Decimal("0.2000"))

        self.assertAlmostEqual(
            ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source_1.source.id)
            ).modifier,
            float(decimal.Decimal("0.2207") / decimal.Decimal("19.7947")),
            places=8,
        )
        self.assertAlmostEqual(
            ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source_2.source.id)
            ).modifier,
            float(decimal.Decimal("0.2207") / decimal.Decimal("19.7947")),
            places=8,
        )

    def test_recalculate_ad_group_amounts_limits(self):
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today() - timedelta(days=1),
            exchange_rate=decimal.Decimal("0.8968"),
        )

        account = magic_mixer.blend(models.Account, currency=constants.Currency.EUR)
        campaign = magic_mixer.blend(models.Campaign, account=account)
        ad_group_1 = magic_mixer.blend(models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)

        ad_group_2 = magic_mixer.blend(models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)

        ad_group_1.settings.update_unsafe(
            None,
            cpc_cc=None,
            local_cpc_cc=None,
            max_cpm=None,
            local_max_cpm=None,
            cpc=decimal.Decimal("20.0000"),
            local_cpc=decimal.Decimal("17.9360"),
            cpm=decimal.Decimal("25.0000"),
            local_cpm=decimal.Decimal("22.4200"),
        )

        ad_group_2.settings.update_unsafe(
            None,
            cpc_cc=decimal.Decimal("10.0000"),
            local_cpc_cc=decimal.Decimal("8.9680"),
            max_cpm=decimal.Decimal("12.5000"),
            local_max_cpm=decimal.Decimal("11.2100"),
            cpc=decimal.Decimal("10.0000"),
            local_cpc=decimal.Decimal("8.9680"),
            cpm=decimal.Decimal("12.5000"),
            local_cpm=decimal.Decimal("11.2100"),
        )

        self.assertEqual(ad_group_1.settings.cpc_cc, None)
        self.assertEqual(ad_group_1.settings.local_cpc_cc, None)
        self.assertEqual(ad_group_1.settings.max_cpm, None)
        self.assertEqual(ad_group_1.settings.local_max_cpm, None)
        self.assertEqual(ad_group_1.settings.cpc, decimal.Decimal("20.0000"))
        self.assertEqual(ad_group_1.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group_1.settings.cpm, decimal.Decimal("25.0000"))
        self.assertEqual(ad_group_1.settings.local_cpm, decimal.Decimal("22.4200"))

        self.assertEqual(ad_group_2.settings.cpc_cc, decimal.Decimal("10.0000"))
        self.assertEqual(ad_group_2.settings.local_cpc_cc, decimal.Decimal("8.9680"))
        self.assertEqual(ad_group_2.settings.max_cpm, decimal.Decimal("12.5000"))
        self.assertEqual(ad_group_2.settings.local_max_cpm, decimal.Decimal("11.2100"))
        self.assertEqual(ad_group_2.settings.cpc, decimal.Decimal("10.0000"))
        self.assertEqual(ad_group_2.settings.local_cpc, decimal.Decimal("8.9680"))
        self.assertEqual(ad_group_2.settings.cpm, decimal.Decimal("12.5000"))
        self.assertEqual(ad_group_2.settings.local_cpm, decimal.Decimal("11.2100"))

        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today(),
            exchange_rate=decimal.Decimal("0.9061"),
        )

        _recalculate_ad_group_amounts(campaign)

        ad_group_1.refresh_from_db()
        ad_group_2.refresh_from_db()

        self.assertEqual(ad_group_1.settings.cpc_cc, None)
        self.assertEqual(ad_group_1.settings.local_cpc_cc, None)
        self.assertEqual(ad_group_1.settings.max_cpm, None)
        self.assertEqual(ad_group_1.settings.local_max_cpm, None)
        self.assertEqual(ad_group_1.settings.cpc, decimal.Decimal("19.7947"))
        self.assertEqual(ad_group_1.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group_1.settings.cpm, decimal.Decimal("24.7434"))
        self.assertEqual(ad_group_1.settings.local_cpm, decimal.Decimal("22.4200"))

        self.assertEqual(ad_group_2.settings.cpc_cc, decimal.Decimal("9.8974"))
        self.assertEqual(ad_group_2.settings.local_cpc_cc, decimal.Decimal("8.9680"))
        self.assertEqual(ad_group_2.settings.max_cpm, decimal.Decimal("12.3717"))
        self.assertEqual(ad_group_2.settings.local_max_cpm, decimal.Decimal("11.2100"))
        self.assertEqual(ad_group_2.settings.cpc, decimal.Decimal("9.8974"))
        self.assertEqual(ad_group_2.settings.local_cpc, decimal.Decimal("8.9680"))
        self.assertEqual(ad_group_2.settings.cpm, decimal.Decimal("12.3717"))
        self.assertEqual(ad_group_2.settings.local_cpm, decimal.Decimal("11.2100"))
