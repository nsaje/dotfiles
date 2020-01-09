from decimal import Decimal

import mock
from django.test import TestCase

import core.features.bid_modifiers
import core.models
import dash.constants
import dash.features.geolocation
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import constants
from . import actions


class ActionsTest(TestCase):
    def test_adjust_bid_modifier(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad = magic_mixer.blend(core.models.ContentAd)
        source = magic_mixer.blend(core.models.Source)
        magic_mixer.blend(dash.features.geolocation.Geolocation, key="USA", type="co")
        magic_mixer.blend(dash.features.geolocation.Geolocation, key="US-01", type="re")
        magic_mixer.blend(dash.features.geolocation.Geolocation, key="123", type="dma")
        test_cases = [
            {
                "target_type": constants.TargetType.AD,
                "target": str(ad.id),
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.AD,
                "bid_modifier_target": str(ad.id),
            },
            {
                "target_type": constants.TargetType.PUBLISHER,
                "target": "publisher1.com__" + str(source.id),
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
                "bid_modifier_target": "publisher1.com",
                "source": source,
            },
            {
                "target_type": constants.TargetType.DEVICE,
                "target": str(dash.constants.DeviceType.DESKTOP),
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.DEVICE,
                "bid_modifier_target": str(dash.constants.DeviceType.DESKTOP),
            },
            {
                "target_type": constants.TargetType.COUNTRY,
                "target": "USA",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.COUNTRY,
                "bid_modifier_target": "USA",
            },
            {
                "target_type": constants.TargetType.STATE,
                "target": "US-01",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.STATE,
                "bid_modifier_target": "US-01",
            },
            {
                "target_type": constants.TargetType.DMA,
                "target": "123",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.DMA,
                "bid_modifier_target": "123",
            },
            {
                "target_type": constants.TargetType.OS,
                "target": "WinPhone",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM,
                "bid_modifier_target": "winphone",
            },
            {
                "target_type": constants.TargetType.SOURCE,
                "target": str(source.id),
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.SOURCE,
                "bid_modifier_target": str(source.id),
            },
        ]
        test_functions = [
            self._test_adjust_bid_modifier_increase_new,
            self._test_adjust_bid_modifier_increase,
            self._test_adjust_bid_modifier_decrease_new,
            self._test_adjust_bid_modifier_decrease,
        ]

        for case in test_cases:
            for fn in test_functions:
                fn(ad_group, **case)
                core.features.bid_modifiers.BidModifier.objects.all().delete()

    def _test_adjust_bid_modifier_increase_new(
        self, ad_group, target_type, target, bid_modifier_type, bid_modifier_target, source=None
    ):
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.8,
            change_limit=2.0,
        )

        self.assertFalse(core.features.bid_modifiers.BidModifier.objects.exists())

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier = core.features.bid_modifiers.BidModifier.objects.get(
            ad_group=ad_group, type=bid_modifier_type, target=bid_modifier_target, source=source
        )
        self.assertEqual(1.8, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(2.0, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

    def _test_adjust_bid_modifier_increase(
        self, ad_group, target_type, target, bid_modifier_type, bid_modifier_target, source=None
    ):
        bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=ad_group,
            type=bid_modifier_type,
            target=bid_modifier_target,
            source=source,
            source_slug=source.bidder_slug if source else "",
            modifier=1.7,
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.2,
            change_limit=2.0,
        )

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.9, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(2.0, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(2.0, bid_modifier.modifier)
        self.assertFalse(update.has_changes())

    def _test_adjust_bid_modifier_decrease_new(
        self, ad_group, target_type, target, bid_modifier_type, bid_modifier_target, source=None
    ):
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.DECREASE_BID_MODIFIER,
            change_step=0.3,
            change_limit=0.5,
        )

        self.assertFalse(core.features.bid_modifiers.BidModifier.objects.exists())

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier = core.features.bid_modifiers.BidModifier.objects.get(
            ad_group=ad_group, type=bid_modifier_type, target=bid_modifier_target, source=source
        )
        self.assertEqual(0.7, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(0.5, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

    def _test_adjust_bid_modifier_decrease(
        self, ad_group, target_type, target, bid_modifier_type, bid_modifier_target, source=None
    ):
        bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=ad_group,
            type=bid_modifier_type,
            target=bid_modifier_target,
            source=source,
            source_slug=source.bidder_slug if source else "",
            modifier=1.9,
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.DECREASE_BID_MODIFIER,
            change_step=0.2,
            change_limit=1.6,
        )

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.7, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.6, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.6, bid_modifier.modifier)
        self.assertFalse(update.has_changes())

    def test_adjust_bid_modifier_unsupported_action(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        rule = magic_mixer.blend(Rule, action_type=constants.ActionType.DECREASE_BUDGET)
        with self.assertRaisesRegexp(Exception, "Invalid bid modifier action type"):
            actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)

    def test_adjust_publisher_bid_modifier_invalid_source_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.PUBLISHER, action_type=constants.ActionType.INCREASE_BID_MODIFIER
        )
        with self.assertRaisesRegexp(Exception, "Source matching query does not exist."):
            actions.adjust_bid_modifier("publisher1.com__" + str(123), rule, ad_group)

    def test_adjust_ad_bid_modifier_invalid_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.AD, action_type=constants.ActionType.INCREASE_BID_MODIFIER
        )
        with self.assertRaisesRegexp(
            core.features.bid_modifiers.exceptions.BidModifierTargetInvalid, "Invalid Content Ad"
        ):
            actions.adjust_bid_modifier("123", rule, ad_group)

    def test_adjust_source_bid_modifier_invalid_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.SOURCE, action_type=constants.ActionType.INCREASE_BID_MODIFIER
        )
        with self.assertRaisesRegexp(core.features.bid_modifiers.exceptions.BidModifierTargetInvalid, "Invalid Source"):
            actions.adjust_bid_modifier("123", rule, ad_group)

    def test_adjust_ad_group_bid_cpc_increase(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPC)
        ad_group.settings.update(None, local_cpc_cc=Decimal("0.5"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.INCREASE_BID,
            change_step=0.2,
            change_limit=0.8,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.7"), ad_group.settings.local_cpc_cc)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.8"), ad_group.settings.local_cpc_cc)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.8"), ad_group.settings.local_cpc_cc)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("0.8"), ad_group.settings.cpc_cc)
        self.assertIsNone(ad_group.settings.max_cpm)
        self.assertIsNone(ad_group.settings.local_max_cpm)

    def test_adjust_ad_group_bid_cpc_decrease(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPC)
        ad_group.settings.update(None, local_cpc_cc=Decimal("0.5"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.DECREASE_BID,
            change_step=0.2,
            change_limit=0.2,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.3"), ad_group.settings.local_cpc_cc)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.2"), ad_group.settings.local_cpc_cc)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.2"), ad_group.settings.local_cpc_cc)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("0.2"), ad_group.settings.cpc_cc)
        self.assertIsNone(ad_group.settings.max_cpm)
        self.assertIsNone(ad_group.settings.local_max_cpm)

    def test_adjust_ad_group_bid_cpm_increase(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPM)
        ad_group.settings.update(None, local_max_cpm=Decimal("1.5"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.INCREASE_BID,
            change_step=0.2,
            change_limit=1.8,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.7"), ad_group.settings.local_max_cpm)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.8"), ad_group.settings.local_max_cpm)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.8"), ad_group.settings.local_max_cpm)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("1.8"), ad_group.settings.max_cpm)
        self.assertIsNone(ad_group.settings.cpc_cc)
        self.assertIsNone(ad_group.settings.local_cpc_cc)

    def test_adjust_ad_group_bid_cpm_decrease(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPM)
        ad_group.settings.update(None, local_max_cpm=Decimal("1.5"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.DECREASE_BID,
            change_step=0.2,
            change_limit=1.2,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.3"), ad_group.settings.local_max_cpm)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.2"), ad_group.settings.local_max_cpm)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.2"), ad_group.settings.local_max_cpm)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("1.2"), ad_group.settings.max_cpm)
        self.assertIsNone(ad_group.settings.cpc_cc)
        self.assertIsNone(ad_group.settings.local_cpc_cc)

    def test_adjust_ad_group_bid_invalid_target_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule)

        with self.assertRaisesRegexp(Exception, "Invalid ad group bid adjustment target"):
            actions.adjust_bid(str(ad_group.id + 1), rule, ad_group)

    def test_adjust_bid_unsupported_action(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, action_type=constants.ActionType.INCREASE_BID_MODIFIER)

        with self.assertRaisesRegexp(Exception, "Invalid bid action type"):
            actions.adjust_bid(str(ad_group.id), rule, ad_group)

    @mock.patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_adjust_ad_group_autopilot_budget_increase(self, mock_recalculate_budgets):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.settings.update(
            None,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            local_autopilot_daily_budget=Decimal("150"),
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.INCREASE_BUDGET,
            change_step=20,
            change_limit=180,
        )

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("170"), ad_group.settings.local_autopilot_daily_budget)
        self.assertTrue(update.has_changes())

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("180"), ad_group.settings.local_autopilot_daily_budget)
        self.assertTrue(update.has_changes())

        self.assertEqual(3, mock_recalculate_budgets.call_count)

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("180"), ad_group.settings.local_autopilot_daily_budget)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("180"), ad_group.settings.autopilot_daily_budget)
        self.assertEqual(3, mock_recalculate_budgets.call_count)

    @mock.patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_adjust_ad_group_autopilot_budget_decrease(self, mock_recalculate_budgets):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPC)
        ad_group.settings.update(
            None,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            local_autopilot_daily_budget=Decimal("150"),
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.DECREASE_BUDGET,
            change_step=20,
            change_limit=120,
        )

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("130"), ad_group.settings.local_autopilot_daily_budget)
        self.assertTrue(update.has_changes())

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("120"), ad_group.settings.local_autopilot_daily_budget)
        self.assertTrue(update.has_changes())

        self.assertEqual(3, mock_recalculate_budgets.call_count)

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("120"), ad_group.settings.local_autopilot_daily_budget)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("120"), ad_group.settings.autopilot_daily_budget)
        self.assertEqual(3, mock_recalculate_budgets.call_count)

    def test_adjust_ad_group_autopilot_budget_invalid_target_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule)

        with self.assertRaisesRegexp(Exception, "Invalid ad group autopilot budget adjustment target"):
            actions.adjust_autopilot_daily_budget(str(ad_group.id + 1), rule, ad_group)

    def test_adjust_ad_group_autopilot_budget_inactive(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule)

        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
        with self.assertRaisesRegexp(Exception, "Budget autopilot inactive"):
            actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)

        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC)
        with self.assertRaisesRegexp(Exception, "Budget autopilot inactive"):
            actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)

    def test_adjust_autopilot_budget_unsupported_action(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, action_type=constants.ActionType.BLACKLIST)

        with self.assertRaisesRegexp(Exception, "Invalid budget action type"):
            actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)

    def test_turn_off_ad_group(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        self.assertEqual(dash.constants.AdGroupSettingsState.ACTIVE, ad_group.settings.state)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.TURN_OFF
        )

        update = actions.turn_off(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(dash.constants.AdGroupSettingsState.INACTIVE, ad_group.settings.state)
        self.assertTrue(update.has_changes())

        update = actions.turn_off(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(dash.constants.AdGroupSettingsState.INACTIVE, ad_group.settings.state)
        self.assertFalse(update.has_changes())

    def test_turn_off_ad_group_invalid_target_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.AD_GROUP, action_type=constants.ActionType.TURN_OFF
        )

        with self.assertRaisesRegexp(Exception, "Invalid ad group turn off target"):
            actions.turn_off(str(ad_group.id + 1), rule, ad_group)

    def test_turn_off_ad(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group)
        self.assertEqual(dash.constants.ContentAdSourceState.ACTIVE, ad.state)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.AD, action_type=constants.ActionType.TURN_OFF)

        update = actions.turn_off(str(ad.id), rule, ad_group)
        ad.refresh_from_db()
        self.assertEqual(dash.constants.ContentAdSourceState.INACTIVE, ad.state)
        self.assertTrue(update.has_changes())

        update = actions.turn_off(str(ad.id), rule, ad_group)
        ad.refresh_from_db()
        self.assertEqual(dash.constants.ContentAdSourceState.INACTIVE, ad.state)
        self.assertFalse(update.has_changes())

    def test_turn_off_ad_invalid_target_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group)
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.AD, action_type=constants.ActionType.TURN_OFF)

        with self.assertRaisesRegexp(Exception, "Invalid ad turn off target"):
            actions.turn_off(str(ad.id + 1), rule, ad_group)

    @mock.patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_turn_off_ad_group_source(self, mock_recalculate_budgets):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource, source=source, ad_group=ad_group)
        ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.assertEqual(dash.constants.AdGroupSourceSettingsState.ACTIVE, ad_group_source.settings.state)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.SOURCE, action_type=constants.ActionType.TURN_OFF
        )

        update = actions.turn_off(str(source.id), rule, ad_group)
        ad_group_source.refresh_from_db()
        self.assertEqual(dash.constants.AdGroupSourceSettingsState.INACTIVE, ad_group_source.settings.state)
        self.assertTrue(update.has_changes())
        mock_recalculate_budgets.assert_called_once()

        update = actions.turn_off(str(source.id), rule, ad_group)
        ad_group_source.refresh_from_db()
        self.assertEqual(dash.constants.AdGroupSourceSettingsState.INACTIVE, ad_group_source.settings.state)
        self.assertFalse(update.has_changes())
        mock_recalculate_budgets.assert_called_once()

    def test_turn_off_source_invalid_target_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource, source=source, ad_group=ad_group)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.SOURCE, action_type=constants.ActionType.TURN_OFF
        )

        with self.assertRaisesRegexp(Exception, "Invalid source turn off target"):
            actions.turn_off(str(ad_group_source.id + 1), rule, ad_group)

    def test_turn_off_unsupported_action(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, action_type=constants.ActionType.BLACKLIST)

        with self.assertRaisesRegexp(Exception, "Invalid action type for turning off"):
            actions.turn_off(str(ad_group.id), rule, ad_group)
