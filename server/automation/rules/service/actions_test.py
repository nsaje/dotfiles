from django.test import TestCase

import core.features.bid_modifiers
import core.models
from utils.magic_mixer import magic_mixer

from .. import Rule
from .. import constants
from . import actions


class ActionsTest(TestCase):
    def test_adjust_publisher_bid_modifier_increase_new(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.8,
            change_limit=2.0,
        )

        self.assertFalse(core.features.bid_modifiers.BidModifier.objects.exists())

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier = core.features.bid_modifiers.BidModifier.objects.get(
            ad_group=ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
            target="publisher1.com",
            source=source,
        )
        self.assertEqual(1.8, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(2.0, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

    def test_adjust_publisher_bid_modifier_increase(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
            target="publisher1.com",
            source=source,
            source_slug=source.bidder_slug,
            modifier=1.7,
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.INCREASE_BID_MODIFIER,
            change_step=0.2,
            change_limit=2.0,
        )

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.9, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(2.0, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(2.0, bid_modifier.modifier)
        self.assertFalse(update.has_changes())

    def test_adjust_publisher_bid_modifier_decrease_new(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.DECREASE_BID_MODIFIER,
            change_step=0.3,
            change_limit=0.5,
        )

        self.assertFalse(core.features.bid_modifiers.BidModifier.objects.exists())

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier = core.features.bid_modifiers.BidModifier.objects.get(
            ad_group=ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
            target="publisher1.com",
            source=source,
        )
        self.assertEqual(0.7, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(0.5, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

    def test_adjust_publisher_bid_modifier_decrease(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
            target="publisher1.com",
            source=source,
            source_slug=source.bidder_slug,
            modifier=1.9,
        )
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.DECREASE_BID_MODIFIER,
            change_step=0.2,
            change_limit=1.6,
        )

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.7, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.6, bid_modifier.modifier)
        self.assertTrue(update.has_changes())

        update = actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
        bid_modifier.refresh_from_db()
        self.assertEqual(1.6, bid_modifier.modifier)
        self.assertFalse(update.has_changes())

    def test_adjust_publisher_bid_modifier_unsupported_action(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        rule = magic_mixer.blend(
            Rule,
            target_type=constants.TargetType.PUBLISHER,
            action_type=constants.ActionType.DECREASE_BUDGET,
            change_step=0.2,
            change_limit=1.6,
        )

        with self.assertRaises(Exception):
            actions.adjust_bid_modifier("publisher1.com__" + str(source.id), rule, ad_group)
