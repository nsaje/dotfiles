from decimal import Decimal

from django.test import TestCase

import dash.constants
import stats.constants
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
            source_slug=source.bidder_slug,
            target="pub1.com",
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


class DeliveryAugmenterTest(TestCase):
    def setUp(self):
        ad_group = magic_mixer.blend(models.AdGroup, id=1)
        source = magic_mixer.blend(models.Source, id=1)
        add_non_publisher_bid_modifiers(ad_group=ad_group, source=source)
        self.bid_modifier = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=ad_group,
            source=source,
            source_slug=source.bidder_slug,
            target=str(dash.constants.DeviceType.DESKTOP),
            modifier=0.5,
            type=bid_modifiers.constants.BidModifierType.DEVICE,
        )
        ad_group_source = magic_mixer.blend(models.AdGroupSource, source=source, ad_group=ad_group)
        ad_group_source.settings.update(None, cpc_cc=Decimal("1.5"), cpm=Decimal("2.5"), skip_validation=True)
        self.user = magic_mixer.blend_user()

        ad_group = models.AdGroup.objects.all().first()
        self.delivery_loader = loaders.DeliveryLoader(
            ad_group, self.user, breakdown=[stats.constants.DeliveryDimension.DEVICE]
        )
        self.augmenter = augmenter.get_augmenter_for_dimension("device_type")
        self.report_augmenter = augmenter.get_report_augmenter_for_dimension("device_type", None)

    def test_augmenter_bid_modifiers(self):
        row = {"bid_modifier_id": self.bid_modifier.id}
        self.augmenter([row], self.delivery_loader)
        self.assertDictEqual(
            row,
            {
                "bid_modifier_id": self.bid_modifier.id,
                "device_type": dash.constants.DeviceType.DESKTOP,
                "bid_modifier": {
                    "id": self.bid_modifier.id,
                    "type": "DEVICE",
                    "source_slug": self.bid_modifier.source_slug,
                    "target": "DESKTOP",
                    "modifier": self.bid_modifier.modifier,
                },
                "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
            },
        )

    def test_augmenter_no_bid_modifier_data(self):
        row = {"device_type": dash.constants.DeviceType.MOBILE}
        self.augmenter([row], self.delivery_loader)
        self.assertDictEqual(
            row,
            {
                "device_type": dash.constants.DeviceType.MOBILE,
                "bid_modifier": {
                    "id": None,
                    "type": "DEVICE",
                    "source_slug": None,
                    "target": "MOBILE",
                    "modifier": None,
                },
                "editable_fields": {"bid_modifier": {"enabled": True, "message": None}},
            },
        )

    def test_augmenter_no_bid_modifier_data_invalid_target(self):
        row = {"device_type": None}
        self.augmenter([row], self.delivery_loader)
        self.assertDictEqual(
            row, {"device_type": None, "editable_fields": {"bid_modifier": {"enabled": True, "message": None}}}
        )

    def test_report_augmenter_bid_modifiers(self):
        row = {"bid_modifier_id": self.bid_modifier.id}
        self.report_augmenter([row], self.delivery_loader)
        self.assertEqual(0.5, row["bid_modifier"])

    def test_report_augmenter_no_bid_modifier_data(self):
        row = row = {"device_type": dash.constants.DeviceType.MOBILE}
        self.report_augmenter([row], self.delivery_loader)
        self.assertEqual(None, row["bid_modifier"])
