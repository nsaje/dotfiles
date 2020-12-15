from collections import defaultdict
from decimal import Decimal

import mock
from django.test import TestCase
from parameterized import param
from parameterized import parameterized

import core.features.bid_modifiers
import core.features.publisher_groups
import core.models
import dash.constants
import dash.features.geolocation
import dash.publisher_helpers
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import constants
from . import actions
from . import exceptions


class BidModifiersParameterized(TestCase):
    TEST_CASES = [
        param(
            "ad",
            **{
                "target_type": constants.TargetType.AD,
                "target": "9999",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.AD,
                "bid_modifier_target": "9999",
                "source": False,
            }
        ),
        param(
            "publisher",
            **{
                "target_type": constants.TargetType.PUBLISHER,
                "target": "publisher1.com__" + "9999",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
                "bid_modifier_target": "publisher1.com",
                "source": True,
            }
        ),
        param(
            "device",
            **{
                "target_type": constants.TargetType.DEVICE,
                "target": str(dash.constants.DeviceType.DESKTOP),
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.DEVICE,
                "bid_modifier_target": str(dash.constants.DeviceType.DESKTOP),
                "source": False,
            }
        ),
        param(
            "country",
            **{
                "target_type": constants.TargetType.COUNTRY,
                "target": "USA",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.COUNTRY,
                "bid_modifier_target": "USA",
                "source": False,
            }
        ),
        param(
            "state",
            **{
                "target_type": constants.TargetType.STATE,
                "target": "US-01",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.STATE,
                "bid_modifier_target": "US-01",
                "source": False,
            }
        ),
        param(
            "dma",
            **{
                "target_type": constants.TargetType.DMA,
                "target": "123",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.DMA,
                "bid_modifier_target": "123",
                "source": False,
            }
        ),
        param(
            "os",
            **{
                "target_type": constants.TargetType.OS,
                "target": "WinPhone",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM,
                "bid_modifier_target": "winphone",
                "source": False,
            }
        ),
        param(
            "environment",
            **{
                "target_type": constants.TargetType.ENVIRONMENT,
                "target": "site",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.ENVIRONMENT,
                "bid_modifier_target": "site",
                "source": False,
            }
        ),
        param(
            "source",
            **{
                "target_type": constants.TargetType.SOURCE,
                "target": "9999",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.SOURCE,
                "bid_modifier_target": "9999",
                "source": False,
            }
        ),
        param(
            "placement",
            **{
                "target_type": constants.TargetType.PLACEMENT,
                "target": dash.publisher_helpers.create_placement_id("zemanta.com", "9999", "100001-1001633"),
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.PLACEMENT,
                "bid_modifier_target": dash.publisher_helpers.create_placement_id(
                    "zemanta.com", "9999", "100001-1001633"
                ),
                "source": True,
            }
        ),
        param(
            "browser",
            **{
                "target_type": constants.TargetType.BROWSER,
                "target": "CHROME",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.BROWSER,
                "bid_modifier_target": "CHROME",
                "source": False,
            }
        ),
        param(
            "connection_type",
            **{
                "target_type": constants.TargetType.CONNECTION_TYPE,
                "target": "cellular",
                "bid_modifier_type": core.features.bid_modifiers.constants.BidModifierType.CONNECTION_TYPE,
                "bid_modifier_target": "cellular",
                "source": False,
            }
        ),
    ]

    def setUp(self):
        campaign = magic_mixer.blend(core.models.Campaign)
        campaign.settings.update_unsafe(None, autopilot=False)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        self.ad_group.settings.update_unsafe(
            None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE
        )
        magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group, id=9999)
        self.source = magic_mixer.blend(core.models.Source, id=9999)
        magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group, source=self.source)
        magic_mixer.blend(dash.features.geolocation.Geolocation, key="USA", type="co")
        magic_mixer.blend(dash.features.geolocation.Geolocation, key="US-01", type="re")
        magic_mixer.blend(dash.features.geolocation.Geolocation, key="123", type="dma")

    @parameterized.expand(TEST_CASES)
    def test_adjust_bid_modifier_increase_new(
        self, _, target_type, target, bid_modifier_type, bid_modifier_target, source=False
    ):
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.8,
            change_limit=2.0,
        )

        self.assertFalse(core.features.bid_modifiers.BidModifier.objects.exists())

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier = core.features.bid_modifiers.BidModifier.objects.get(
            ad_group=self.ad_group,
            type=bid_modifier_type,
            target=bid_modifier_target,
            source=self.source if source else None,
        )
        self.assertEqual(1.8, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(2.0, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

    @parameterized.expand(TEST_CASES)
    def test_adjust_bid_modifier_increase(
        self, _, target_type, target, bid_modifier_type, bid_modifier_target, source=False
    ):
        bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=bid_modifier_type,
            target=bid_modifier_target,
            source=self.source if source else None,
            source_slug=self.source.bidder_slug if source else "",
            modifier=1.7,
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.2,
            change_limit=2.0,
        )

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.9, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(2.0, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(2.0, bid_modifier.modifier)
        self.assertFalse(update.has_changes())

    @parameterized.expand(TEST_CASES)
    def test_adjust_bid_modifier_increase_over_limit(
        self, _, target_type, target, bid_modifier_type, bid_modifier_target, source=False
    ):
        bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=bid_modifier_type,
            target=bid_modifier_target,
            source=self.source if source else None,
            source_slug=self.source.bidder_slug if source else "",
            modifier=1.7,
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.2,
            change_limit=1.5,
        )

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.7, bid_modifier.modifier)
        self.assertFalse(update.has_changes())

    @parameterized.expand(TEST_CASES)
    def test_adjust_bid_modifier_decrease_new(
        self, _, target_type, target, bid_modifier_type, bid_modifier_target, source=False
    ):
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.DECREASE_BID_MODIFIER,
            change_step=0.3,
            change_limit=0.5,
        )

        self.assertFalse(core.features.bid_modifiers.BidModifier.objects.exists())

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier = core.features.bid_modifiers.BidModifier.objects.get(
            ad_group=self.ad_group,
            type=bid_modifier_type,
            target=bid_modifier_target,
            source=self.source if source else None,
        )
        self.assertEqual(0.7, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(0.5, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

    @parameterized.expand(TEST_CASES)
    def test_adjust_bid_modifier_decrease(
        self, _, target_type, target, bid_modifier_type, bid_modifier_target, source=False
    ):
        bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=bid_modifier_type,
            target=bid_modifier_target,
            source=self.source if source else None,
            source_slug=self.source.bidder_slug if source else "",
            modifier=1.9,
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.DECREASE_BID_MODIFIER,
            change_step=0.2,
            change_limit=1.6,
        )

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.7, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.6, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.6, bid_modifier.modifier)
        self.assertFalse(update.has_changes())

    @parameterized.expand(TEST_CASES)
    def test_adjust_bid_modifier_decrease_under_limit(
        self, _, target_type, target, bid_modifier_type, bid_modifier_target, source=False
    ):
        bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=bid_modifier_type,
            target=bid_modifier_target,
            source=self.source if source else None,
            source_slug=self.source.bidder_slug if source else "",
            modifier=1.7,
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=target_type,
            action_type=constants.ActionType.DECREASE_BID_MODIFIER,
            change_step=0.2,
            change_limit=2.0,
        )

        update = actions.adjust_bid_modifier(target, rule, self.ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.7, bid_modifier.modifier)
        self.assertFalse(update.has_changes())


class ActionsTest(TestCase):
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
        campaign = magic_mixer.blend(core.models.Campaign)
        campaign.settings.update_unsafe(None, autopilot=False)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.SOURCE, action_type=constants.ActionType.INCREASE_BID_MODIFIER
        )
        with self.assertRaisesRegexp(core.features.bid_modifiers.exceptions.BidModifierTargetInvalid, "Invalid Source"):
            actions.adjust_bid_modifier("123", rule, ad_group)

    def test_adjust_ad_group_bid_cpc_increase(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPC)
        ad_group.settings.update(None, cpc=Decimal("0.5"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.INCREASE_BID,
            change_step=0.2,
            change_limit=0.8,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.7"), ad_group.settings.cpc)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.8"), ad_group.settings.cpc)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.8"), ad_group.settings.cpc)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("0.8"), ad_group.settings.local_cpc)

    def test_adjust_ad_group_bid_cpc_increase_over_limit(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPC)
        ad_group.settings.update(None, cpc=Decimal("0.6"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.INCREASE_BID,
            change_step=0.2,
            change_limit=0.5,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.6"), ad_group.settings.cpc)
        self.assertFalse(update.has_changes())

    def test_adjust_ad_group_bid_cpc_decrease(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPC)
        ad_group.settings.update(None, cpc=Decimal("0.5"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.DECREASE_BID,
            change_step=0.2,
            change_limit=0.2,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.3"), ad_group.settings.cpc)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.2"), ad_group.settings.cpc)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.2"), ad_group.settings.cpc)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("0.2"), ad_group.settings.local_cpc)

    def test_adjust_ad_group_bid_cpc_decrease_below_limit(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPC)
        ad_group.settings.update(None, cpc=Decimal("0.4"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.DECREASE_BID,
            change_step=0.2,
            change_limit=0.5,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("0.4"), ad_group.settings.cpc)
        self.assertFalse(update.has_changes())

    def test_adjust_ad_group_bid_cpm_increase(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPM)
        ad_group.settings.update(None, cpm=Decimal("1.5"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.INCREASE_BID,
            change_step=0.2,
            change_limit=1.8,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.7"), ad_group.settings.cpm)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.8"), ad_group.settings.cpm)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.8"), ad_group.settings.cpm)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("1.8"), ad_group.settings.local_cpm)

    def test_adjust_ad_group_bid_cpm_increase_over_limit(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPM)
        ad_group.settings.update(None, cpm=Decimal("1.6"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.INCREASE_BID,
            change_step=0.2,
            change_limit=1.5,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.6"), ad_group.settings.cpm)
        self.assertFalse(update.has_changes())

    def test_adjust_ad_group_bid_cpm_decrease(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPM)
        ad_group.settings.update(None, cpm=Decimal("1.5"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.DECREASE_BID,
            change_step=0.2,
            change_limit=1.2,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.3"), ad_group.settings.cpm)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.2"), ad_group.settings.cpm)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.2"), ad_group.settings.cpm)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("1.2"), ad_group.settings.local_cpm)

    def test_adjust_ad_group_bid_cpm_decrease_below_limit(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, bidding_type=dash.constants.BiddingType.CPM)
        ad_group.settings.update(None, cpm=Decimal("1.4"))
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.DECREASE_BID,
            change_step=0.2,
            change_limit=1.5,
        )

        update = actions.adjust_bid(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.4"), ad_group.settings.cpm)
        self.assertFalse(update.has_changes())

    def test_adjust_ad_group_bid_invalid_target_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule)

        with self.assertRaisesRegexp(Exception, "Invalid ad group bid adjustment target"):
            actions.adjust_bid(str(-1), rule, ad_group)

    def test_adjust_bid_unsupported_action(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, action_type=constants.ActionType.INCREASE_BID_MODIFIER)

        with self.assertRaisesRegexp(Exception, "Invalid bid action type"):
            actions.adjust_bid(str(ad_group.id), rule, ad_group)

    @mock.patch("automation.autopilot.recalculate_ad_group_budgets")
    def test_adjust_ad_group_autopilot_budget_increase(self, mock_recalculate_budgets):
        campaign = magic_mixer.blend(core.models.Campaign, account__agency__uses_realtime_autopilot=True)
        campaign.settings.update_unsafe(None, autopilot=False)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update(
            None,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            autopilot_daily_budget=Decimal("150"),
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
        self.assertEqual(Decimal("170"), ad_group.settings.autopilot_daily_budget)
        self.assertTrue(update.has_changes())

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("180"), ad_group.settings.autopilot_daily_budget)
        self.assertTrue(update.has_changes())

        mock_recalculate_budgets.assert_not_called()

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("180"), ad_group.settings.autopilot_daily_budget)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("180"), ad_group.settings.local_autopilot_daily_budget)
        mock_recalculate_budgets.assert_not_called()

    @mock.patch("automation.autopilot.recalculate_ad_group_budgets")
    def test_adjust_ad_group_autopilot_budget_increase_over_limit(self, mock_recalculate_budgets):
        campaign = magic_mixer.blend(core.models.Campaign, account__agency__uses_realtime_autopilot=True)
        campaign.settings.update_unsafe(None, autopilot=False)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update(
            None,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            autopilot_daily_budget=Decimal("180"),
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.INCREASE_BUDGET,
            change_step=20,
            change_limit=150,
        )

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("180"), ad_group.settings.autopilot_daily_budget)
        self.assertFalse(update.has_changes())

    @mock.patch("automation.autopilot.recalculate_ad_group_budgets")
    def test_adjust_ad_group_autopilot_budget_decrease(self, mock_recalculate_budgets):
        campaign = magic_mixer.blend(core.models.Campaign, account__agency__uses_realtime_autopilot=True)
        campaign.settings.update_unsafe(None, autopilot=False)
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign=campaign, bidding_type=dash.constants.BiddingType.CPC
        )
        ad_group.settings.update(
            None,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            autopilot_daily_budget=Decimal("150"),
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
        self.assertEqual(Decimal("130"), ad_group.settings.autopilot_daily_budget)
        self.assertTrue(update.has_changes())

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("120"), ad_group.settings.autopilot_daily_budget)
        self.assertTrue(update.has_changes())

        mock_recalculate_budgets.assert_not_called()

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("120"), ad_group.settings.autopilot_daily_budget)
        self.assertFalse(update.has_changes())

        self.assertEqual(Decimal("120"), ad_group.settings.local_autopilot_daily_budget)
        mock_recalculate_budgets.assert_not_called()

    @mock.patch("automation.autopilot.recalculate_ad_group_budgets")
    def test_adjust_ad_group_autopilot_budget_decrease_under_limit(self, mock_recalculate_budgets):
        campaign = magic_mixer.blend(core.models.Campaign, account__agency__uses_realtime_autopilot=True)
        campaign.settings.update_unsafe(None, autopilot=False)
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign=campaign, bidding_type=dash.constants.BiddingType.CPC
        )
        ad_group.settings.update(
            None,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            autopilot_daily_budget=Decimal("140"),
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.AD_GROUP,
            action_type=constants.ActionType.DECREASE_BUDGET,
            change_step=20,
            change_limit=150,
        )

        update = actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("140"), ad_group.settings.autopilot_daily_budget)
        self.assertFalse(update.has_changes())

    def test_adjust_ad_group_autopilot_budget_invalid_target_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule)

        with self.assertRaisesRegexp(Exception, "Invalid ad group autopilot budget adjustment target"):
            actions.adjust_autopilot_daily_budget(str(-1), rule, ad_group)

    def test_adjust_ad_group_autopilot_campaign_fail(self):
        campaign = magic_mixer.blend(core.models.Campaign)
        campaign.settings.update_unsafe(None, autopilot=True)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        rule = magic_mixer.blend(Rule, action_type=constants.ActionType.INCREASE_BUDGET)

        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
        with self.assertRaisesRegexp(exceptions.CampaignAutopilotActive, "Campaign autopilot must not be active"):
            actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)

        ad_group.settings.update_unsafe(
            None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        )
        with self.assertRaisesRegexp(exceptions.CampaignAutopilotActive, "Campaign autopilot must not be active"):
            actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)

    def test_adjust_ad_group_autopilot_budget_fail(self):
        campaign = magic_mixer.blend(core.models.Campaign)
        campaign.settings.update_unsafe(None, autopilot=False)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        rule = magic_mixer.blend(Rule, action_type=constants.ActionType.INCREASE_BUDGET)

        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
        with self.assertRaisesRegexp(exceptions.BudgetAutopilotInactive, "Budget autopilot must be active"):
            actions.adjust_autopilot_daily_budget(str(ad_group.id), rule, ad_group)

        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC)
        with self.assertRaisesRegexp(exceptions.BudgetAutopilotInactive, "Budget autopilot must be active"):
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
            actions.turn_off(str(-1), rule, ad_group)

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
        rule = magic_mixer.blend(Rule, target_type=constants.TargetType.AD, action_type=constants.ActionType.TURN_OFF)

        with self.assertRaisesRegexp(Exception, "Invalid ad turn off target"):
            actions.turn_off(str(-1), rule, ad_group)

    @mock.patch("automation.autopilot.recalculate_ad_group_budgets")
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
        mock_recalculate_budgets.assert_not_called()

        update = actions.turn_off(str(source.id), rule, ad_group)
        ad_group_source.refresh_from_db()
        self.assertEqual(dash.constants.AdGroupSourceSettingsState.INACTIVE, ad_group_source.settings.state)
        self.assertFalse(update.has_changes())
        mock_recalculate_budgets.assert_not_called()

    def test_turn_off_source_invalid_target_id(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(
            Rule, target_type=constants.TargetType.SOURCE, action_type=constants.ActionType.TURN_OFF
        )

        with self.assertRaisesRegexp(Exception, "Invalid source turn off target"):
            actions.turn_off(str(-1), rule, ad_group)

    def test_turn_off_unsupported_action(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        rule = magic_mixer.blend(Rule, action_type=constants.ActionType.BLACKLIST)

        with self.assertRaisesRegexp(Exception, "Invalid action type for turning off"):
            actions.turn_off(str(ad_group.id), rule, ad_group)


@mock.patch("utils.email_helper.send_official_email")
class SendEmailTestCase(TestCase):
    def setUp(self):
        self.agency = magic_mixer.blend(core.models.Agency)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=self.agency)
        self.send_email_recipients = ["user@test.com"]
        self.send_email_subject = "This is test email subject"
        self.send_email_body = "This is test email body"

    def test_send_email(self, mock_send_official_email):

        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            action_type=constants.ActionType.SEND_EMAIL,
            send_email_recipients=self.send_email_recipients,
            send_email_subject=self.send_email_subject,
            send_email_body=self.send_email_body,
        )

        actions.send_email(str(self.ad_group.id), rule, self.ad_group, target_stats=defaultdict(dict))

        mock_send_official_email.assert_called_once_with(
            self.ad_group.campaign.account.agency,
            recipient_list=self.send_email_recipients,
            subject=self.send_email_subject,
            body=self.send_email_body,
        )

    def test_send_email_simple_macro_expansion(self, mock_send_official_email):
        send_email_subject_macro = "Account id: {ACCOUNT_ID}"
        send_email_body_macro = "Clicks: {CLICKS_LAST_30_DAYS}"

        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            action_type=constants.ActionType.SEND_EMAIL,
            send_email_recipients=self.send_email_recipients,
            send_email_subject=send_email_subject_macro,
            send_email_body=send_email_body_macro,
        )

        actions.send_email(
            str(self.ad_group.id),
            rule,
            self.ad_group,
            target_stats={"clicks": {constants.MetricWindow.LAST_30_DAYS: 2000}},
        )

        mock_send_official_email.assert_called_once_with(
            self.ad_group.campaign.account.agency,
            recipient_list=self.send_email_recipients,
            subject=send_email_subject_macro.format(ACCOUNT_ID=self.ad_group.campaign.account_id),
            body=send_email_body_macro.format(CLICKS_LAST_30_DAYS=2000),
        )

    def test_send_email_invalid_target(self, mock_send_official_email):
        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            action_type=constants.ActionType.SEND_EMAIL,
            send_email_recipients=self.send_email_recipients,
            send_email_subject=self.send_email_subject,
            send_email_body=self.send_email_body,
        )

        with self.assertRaisesRegexp(Exception, "Invalid target"):
            actions.send_email(str(-1), rule, self.ad_group, target_stats={})

    def test_send_email_invalid_action(self, mock_send_official_email):
        rule = magic_mixer.blend(Rule, agency=self.agency, action_type=constants.ActionType.BLACKLIST)

        with self.assertRaisesRegexp(Exception, "Invalid action"):
            actions.send_email(str(-1), rule, self.ad_group, target_stats={})


class BlacklistTestCase(TestCase):
    def setUp(self):
        self.agency = magic_mixer.blend(core.models.Agency)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=self.agency)
        self.source = magic_mixer.blend(core.models.Source)

    def test_blacklist_publisher(self):
        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            action_type=constants.ActionType.BLACKLIST,
            target_type=constants.TargetType.PUBLISHER,
        )
        self.assertEqual(self.ad_group.default_blacklist, None)

        actions.blacklist("publisher1.com__" + str(self.source.id), rule, self.ad_group)
        self.assertCountEqual(
            self.ad_group.default_blacklist.entries.all().values("publisher", "include_subdomains", "source"),
            [{"publisher": "publisher1.com", "source": self.source.id, "include_subdomains": False}],
        )

    def test_blacklist_placement(self):
        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            action_type=constants.ActionType.BLACKLIST,
            target_type=constants.TargetType.PLACEMENT,
        )
        self.assertEqual(self.ad_group.default_blacklist, None)

        actions.blacklist("publisher1.com__" + str(self.source.id) + "__00000-00000", rule, self.ad_group)
        self.assertCountEqual(
            self.ad_group.default_blacklist.entries.all().values(
                "publisher", "include_subdomains", "source", "placement"
            ),
            [
                {
                    "publisher": "publisher1.com",
                    "source": self.source.id,
                    "include_subdomains": False,
                    "placement": "00000-00000",
                }
            ],
        )

    def test_invalid_action_type(self):
        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            action_type=constants.ActionType.DECREASE_BID,
            target_type=constants.TargetType.PUBLISHER,
        )

        with self.assertRaisesRegexp(Exception, "Invalid action"):
            actions.blacklist("publisher1.com__" + str(self.source.id), rule, self.ad_group)

    def test_invalid_target_type(self):
        rule = magic_mixer.blend(
            Rule, agency=self.agency, action_type=constants.ActionType.BLACKLIST, target_type=constants.TargetType.AD
        )
        self.assertEqual(self.ad_group.default_blacklist, None)

        with self.assertRaisesRegexp(Exception, "Invalid blacklist target"):
            actions.blacklist("publisher1.com__" + str(self.source.id), rule, self.ad_group)


class AddToPublisherGroupTestCase(TestCase):
    def setUp(self):
        self.agency = magic_mixer.blend(core.models.Agency)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=self.agency)
        self.source = magic_mixer.blend(core.models.Source)
        self.publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=self.ad_group.campaign.account
        )

    def test_add_to_publisher_group(self):
        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            publisher_group=self.publisher_group,
            action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP,
            target_type=constants.TargetType.PUBLISHER,
        )
        self.assertEqual(self.ad_group.default_blacklist, None)
        actions.add_to_publisher_group("publisher1.com__" + str(self.source.id), rule, self.ad_group)
        self.assertCountEqual(
            self.publisher_group.entries.all().values("publisher", "include_subdomains", "source"),
            [{"publisher": "publisher1.com", "source": self.source.id, "include_subdomains": False}],
        )

    def test_add_placement_to_publisher_group(self):
        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            publisher_group=self.publisher_group,
            action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP,
            target_type=constants.TargetType.PLACEMENT,
        )
        self.assertEqual(self.ad_group.default_blacklist, None)
        actions.add_to_publisher_group("publisher1.com__" + str(self.source.id) + "__00000-00000", rule, self.ad_group)
        self.assertCountEqual(
            self.publisher_group.entries.all().values("publisher", "include_subdomains", "source", "placement"),
            [
                {
                    "publisher": "publisher1.com",
                    "source": self.source.id,
                    "include_subdomains": False,
                    "placement": "00000-00000",
                }
            ],
        )

    def test_add_to_publisher_group_twice(self):
        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            publisher_group=self.publisher_group,
            action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP,
            target_type=constants.TargetType.PUBLISHER,
        )
        actions.add_to_publisher_group("publisher1.com__" + str(self.source.id), rule, self.ad_group)
        actions.add_to_publisher_group("publisher1.com__" + str(self.source.id), rule, self.ad_group)
        self.assertCountEqual(
            self.publisher_group.entries.all().values("publisher", "include_subdomains", "source"),
            [{"publisher": "publisher1.com", "source": self.source.id, "include_subdomains": False}],
        )

    def test_invalid_action_type(self):
        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            action_type=constants.ActionType.DECREASE_BID,
            target_type=constants.TargetType.PUBLISHER,
        )

        with self.assertRaisesRegexp(Exception, "Invalid action type for adding to publisher group"):
            actions.add_to_publisher_group("publisher1.com__" + str(self.source.id), rule, self.ad_group)

    def test_invalid_target_type(self):
        rule = magic_mixer.blend(
            Rule,
            agency=self.agency,
            action_type=constants.ActionType.ADD_TO_PUBLISHER_GROUP,
            target_type=constants.TargetType.AD,
        )

        with self.assertRaisesRegexp(Exception, "Invalid add to publisher group target"):
            actions.add_to_publisher_group("publisher1.com__" + str(self.source.id), rule, self.ad_group)
