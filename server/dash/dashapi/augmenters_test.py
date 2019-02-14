from decimal import Decimal

from django.test import TestCase

from core.features import bid_modifiers
from core.features.publisher_bid_modifiers.service_test import add_non_publisher_bid_modifiers
from dash import models
from dash.dashapi import augmenter
from dash.dashapi import loaders
from utils.magic_mixer import magic_mixer


class PublisherAugmenterTest(TestCase):
    def setUp(self):
        ad_group = magic_mixer.blend(models.AdGroup, id=1)
        source = magic_mixer.blend(models.Source, id=1)
        add_non_publisher_bid_modifiers(ad_group=ad_group, source=source)
        magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=ad_group,
            source=source,
            publisher="pub1.com",
            modifier=0.5,
            type=bid_modifiers.constants.BidModifierType.PUBLISHER,
        )
        ad_group_source = magic_mixer.blend(models.AdGroupSource, source=source, ad_group=ad_group)
        ad_group_source.settings.update(None, cpc_cc=Decimal("1.5"), cpm=Decimal("2.5"), skip_validation=True)
        user = magic_mixer.blend_user()

        self.bid_modifier_loader = loaders.PublisherBidModifierLoader(
            models.AdGroup.objects.all().first(),
            models.PublisherGroupEntry.objects.filter(),
            models.PublisherGroupEntry.objects.all(),
            {},
            models.Source.objects.all(),
            user,
        )

        self.augmenter = augmenter.get_augmenter_for_dimension("publisher_id")
        self.report_augmenter = augmenter.get_report_augmenter_for_dimension("publisher_id", None)

    def test_augmenter_bid_modifiers(self):
        row = {"publisher_id": "pub1.com__1", "source_id": 1}
        self.augmenter([row], self.bid_modifier_loader)
        self.assertDictEqual(
            row["bid_modifier"],
            {
                "modifier": 0.5,
                "source_bid_value": {
                    "bid_cpc_value": Decimal("1.5000"),
                    "bid_cpm_value": Decimal("2.5000"),
                    "currency_symbol": "$",
                },
            },
        )

    def test_report_augmenter_bid_modifiers(self):
        row = {"publisher_id": "pub1.com__1", "source_id": 1}
        self.report_augmenter([row], self.bid_modifier_loader)
        self.assertEqual(row["bid_modifier"], 0.5)
