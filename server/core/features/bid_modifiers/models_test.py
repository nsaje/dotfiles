from django.db.utils import IntegrityError
from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import constants
from . import models


class BidModifierTestCase(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.models.AdGroup)
        self.source = magic_mixer.blend(core.models.Source)
        self.target = "1"

    def test_unique_together_with_source_create(self):
        magic_mixer.blend(
            models.BidModifier,
            type=constants.BidModifierType.PUBLISHER,
            ad_group=self.ad_group,
            source=self.source,
            source_slug=self.source.bidder_slug,
            target=self.target,
        )

        with self.assertRaises(IntegrityError):
            magic_mixer.blend(
                models.BidModifier,
                type=constants.BidModifierType.PUBLISHER,
                ad_group=self.ad_group,
                source=self.source,
                source_slug=self.source.bidder_slug,
                target=self.target,
            )

    def test_unique_together_with_source_update(self):
        magic_mixer.blend(
            models.BidModifier,
            type=constants.BidModifierType.PUBLISHER,
            ad_group=self.ad_group,
            source=self.source,
            source_slug=self.source.bidder_slug,
            target=self.target,
        )

        models.BidModifier.objects.update_or_create(
            defaults={"modifier": 7, "source": self.source},
            type=constants.BidModifierType.PUBLISHER,
            ad_group=self.ad_group,
            source_slug=self.source.bidder_slug,
            target=self.target,
        )

        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

    def test_unique_together_without_source_create(self):
        magic_mixer.blend(
            models.BidModifier,
            type=constants.BidModifierType.OPERATING_SYSTEM,
            ad_group=self.ad_group,
            source=None,
            source_slug="",
            target=self.target,
        )

        with self.assertRaises(IntegrityError):
            magic_mixer.blend(
                models.BidModifier,
                type=constants.BidModifierType.OPERATING_SYSTEM,
                ad_group=self.ad_group,
                source=None,
                source_slug="",
                target=self.target,
            )

    def test_unique_together_without_source_update(self):
        magic_mixer.blend(
            models.BidModifier,
            type=constants.BidModifierType.OPERATING_SYSTEM,
            ad_group=self.ad_group,
            source=None,
            source_slug="",
            target=self.target,
        )

        models.BidModifier.objects.update_or_create(
            defaults={"modifier": 7, "source": self.source},
            type=constants.BidModifierType.OPERATING_SYSTEM,
            ad_group=self.ad_group,
            source_slug="",
            target=self.target,
        )

        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

    def test_bid_modifier_update(self):
        magic_mixer.blend(
            models.BidModifier,
            type=constants.BidModifierType.OPERATING_SYSTEM,
            ad_group=self.ad_group,
            source=None,
            source_slug="",
            target=self.target,
        )

        models.BidModifier.objects.update_or_create(
            defaults={"modifier": 7, "source": self.source},
            type=constants.BidModifierType.OPERATING_SYSTEM,
            ad_group=self.ad_group,
            source_slug="",
            target=self.target,
        )

        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

    def test_publisher_bid_modifier_update(self):
        magic_mixer.blend(
            models.BidModifier,
            type=constants.BidModifierType.PUBLISHER,
            ad_group=self.ad_group,
            source=self.source,
            source_slug=self.source.bidder_slug,
            target=self.target,
        )
        magic_mixer.blend(
            models.BidModifier,
            type=constants.BidModifierType.OPERATING_SYSTEM,
            ad_group=self.ad_group,
            source=self.source,
            source_slug=self.source.bidder_slug,
            target=self.target,
        )

        models.BidModifier.objects.filter_publisher_bid_modifiers().update_or_create(
            defaults={"modifier": 7, "type": constants.BidModifierType.PUBLISHER, "source": self.source},
            ad_group=self.ad_group,
            source_slug=self.source.bidder_slug,
            target=self.target,
        )

        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 2)

        with self.assertRaises(models.BidModifier.MultipleObjectsReturned):
            models.BidModifier.objects.update_or_create(
                defaults={"modifier": 7, "type": constants.BidModifierType.PUBLISHER, "source": self.source},
                ad_group=self.ad_group,
                source_slug=self.source.bidder_slug,
                target=self.target,
            )
