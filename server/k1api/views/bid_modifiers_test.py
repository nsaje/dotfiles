import json

import mock
from django.conf import settings
from django.urls import reverse

import core.features.bid_modifiers
import core.features.bid_modifiers.constants
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest


class BidModifiersTest(K1APIBaseTest):
    def setUp(self):
        self.source = magic_mixer.blend(core.models.Source, id=1, bidder_slug="test_source")
        self.bid_modifier_types = list(core.features.bid_modifiers.constants.BidModifierType.get_all())
        super(BidModifiersTest, self).setUp()

    def repr(self, obj):
        return {
            "id": obj.id,
            "ad_group_id": obj.ad_group_id,
            "type": obj.type,
            "target": obj.target,
            "source": obj.source_slug,
            "modifier": obj.modifier,
        }

    def test_get(self):
        test_objs = magic_mixer.cycle(3).blend(
            core.features.bid_modifiers.BidModifier,
            source=None,
            source_slug="",
            target="123",
            type=(t for t in self.bid_modifier_types),
        )
        test_objs.append(
            magic_mixer.blend(
                core.features.bid_modifiers.BidModifier,
                source=self.source,
                source_slug=self.source.bidder_slug,
                target="321",
                type=(t for t in self.bid_modifier_types),
            )
        )
        response = self.client.get(reverse("k1api.bidmodifiers"))
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(data["response"], [self.repr(obj) for obj in test_objs])

    def test_pagination(self):
        test_objs = magic_mixer.cycle(10).blend(
            core.features.bid_modifiers.BidModifier,
            source=self.source,
            source_slug=self.source.bidder_slug,
            modifier=(id for id in range(1, 11)),
            type=(t for t in self.bid_modifier_types),
        )
        response = self.client.get(reverse("k1api.bidmodifiers"), {"marker": test_objs[2].id, "limit": 5})
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(data["response"], [self.repr(obj) for obj in test_objs[3:8]])

    def test_filter_by_type(self):
        test_objs = magic_mixer.cycle(len(self.bid_modifier_types)).blend(
            core.features.bid_modifiers.BidModifier, type=(typ for typ in self.bid_modifier_types)
        )
        ad_type = core.features.bid_modifiers.BidModifierType.AD
        response = self.client.get(reverse("k1api.bidmodifiers"), {"type": ad_type})
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(1, len(data["response"]))
        self.assertEqual(data["response"], [self.repr(obj) for obj in test_objs if obj.type == ad_type])


@mock.patch("django.conf.settings.SOURCE_GROUPS", {settings.HARDCODED_SOURCE_ID_OUTBRAINRTB: [81]})
class BidModifiersGroupsTest(K1APIBaseTest):
    def setUp(self):
        super().setUp()

        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency__uses_source_groups=True)

        self.parent_source = magic_mixer.blend(
            core.models.Source,
            id=settings.HARDCODED_SOURCE_ID_OUTBRAINRTB,
            bidder_slug="main_slug",
            tracking_slug="main_tracking",
        )
        self.grouped_source = magic_mixer.blend(
            core.models.Source, id=81, bidder_slug="sub_slug", tracking_slug="sub_tracking"
        )

        self.source_bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.SOURCE,
            target=str(self.parent_source.id),
            modifier=1.7,
        )
        self.publisher_bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
            source=self.parent_source,
            source_slug=self.parent_source.bidder_slug,
            modifier=1.8,
        )
        self.placement_bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.PLACEMENT,
            source=self.parent_source,
            source_slug=self.parent_source.bidder_slug,
            modifier=1.9,
        )

        # deprecated bid modifiers
        self.deprecated_source_bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.SOURCE,
            target=str(self.grouped_source.id),
            modifier=2.7,
        )
        self.deprecated_publisher_bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
            source=self.grouped_source,
            source_slug=self.grouped_source.bidder_slug,
            modifier=2.8,
        )
        self.deprecated_placement_bid_modifier = magic_mixer.blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=self.ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.PLACEMENT,
            source=self.grouped_source,
            source_slug=self.grouped_source.bidder_slug,
            modifier=2.9,
        )

    def test_get_grouped_bid_modifiers(self):
        response = self.client.get(reverse("k1api.bidmodifiers"))

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 6)

        self.assertCountEqual(
            [
                {
                    "id": self.source_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.source_bid_modifier.target,
                    "type": self.source_bid_modifier.type,
                    "source": self.source_bid_modifier.source_slug,
                    "modifier": self.source_bid_modifier.modifier,
                },
                {
                    "id": self.source_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": str(self.grouped_source.id),
                    "type": self.source_bid_modifier.type,
                    "source": self.source_bid_modifier.source_slug,
                    "modifier": self.source_bid_modifier.modifier,
                },
                {
                    "id": self.publisher_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.publisher_bid_modifier.target,
                    "type": self.publisher_bid_modifier.type,
                    "source": self.publisher_bid_modifier.source_slug,
                    "modifier": self.publisher_bid_modifier.modifier,
                },
                {
                    "id": self.publisher_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.publisher_bid_modifier.target,
                    "type": self.publisher_bid_modifier.type,
                    "source": self.grouped_source.bidder_slug,
                    "modifier": self.publisher_bid_modifier.modifier,
                },
                {
                    "id": self.placement_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.placement_bid_modifier.target,
                    "type": self.placement_bid_modifier.type,
                    "source": self.placement_bid_modifier.source_slug,
                    "modifier": self.placement_bid_modifier.modifier,
                },
                {
                    "id": self.placement_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.placement_bid_modifier.target,
                    "type": self.placement_bid_modifier.type,
                    "source": self.grouped_source.bidder_slug,
                    "modifier": self.placement_bid_modifier.modifier,
                },
            ],
            data,
        )

    def test_get_grouped_bid_modifiers_no_flag(self):
        self.ad_group.campaign.account.agency.uses_source_groups = False
        self.ad_group.campaign.account.agency.save(None)

        response = self.client.get(reverse("k1api.bidmodifiers"))

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 6)

        self.assertCountEqual(
            [
                {
                    "id": self.source_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.source_bid_modifier.target,
                    "type": self.source_bid_modifier.type,
                    "source": self.source_bid_modifier.source_slug,
                    "modifier": self.source_bid_modifier.modifier,
                },
                {
                    "id": self.publisher_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.publisher_bid_modifier.target,
                    "type": self.publisher_bid_modifier.type,
                    "source": self.publisher_bid_modifier.source_slug,
                    "modifier": self.publisher_bid_modifier.modifier,
                },
                {
                    "id": self.placement_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.placement_bid_modifier.target,
                    "type": self.placement_bid_modifier.type,
                    "source": self.placement_bid_modifier.source_slug,
                    "modifier": self.placement_bid_modifier.modifier,
                },
                {
                    "id": self.deprecated_source_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": str(self.grouped_source.id),
                    "type": self.deprecated_source_bid_modifier.type,
                    "source": self.deprecated_source_bid_modifier.source_slug,
                    "modifier": self.deprecated_source_bid_modifier.modifier,
                },
                {
                    "id": self.deprecated_publisher_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.deprecated_publisher_bid_modifier.target,
                    "type": self.deprecated_publisher_bid_modifier.type,
                    "source": self.grouped_source.bidder_slug,
                    "modifier": self.deprecated_publisher_bid_modifier.modifier,
                },
                {
                    "id": self.deprecated_placement_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.deprecated_placement_bid_modifier.target,
                    "type": self.deprecated_placement_bid_modifier.type,
                    "source": self.grouped_source.bidder_slug,
                    "modifier": self.deprecated_placement_bid_modifier.modifier,
                },
            ],
            data,
        )

    def test_get_grouped_bid_modifiers_oen(self):
        self.ad_group.campaign.account = magic_mixer.blend(
            core.models.Account, id=settings.HARDCODED_ACCOUNT_ID_OEN, agency__uses_source_groups=True
        )
        self.ad_group.campaign.save(None)

        response = self.client.get(reverse("k1api.bidmodifiers"))

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 3)

        self.assertCountEqual(
            [
                {
                    "id": self.source_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": str(self.grouped_source.id),
                    "type": self.source_bid_modifier.type,
                    "source": self.source_bid_modifier.source_slug,
                    "modifier": self.source_bid_modifier.modifier,
                },
                {
                    "id": self.publisher_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.publisher_bid_modifier.target,
                    "type": self.publisher_bid_modifier.type,
                    "source": self.grouped_source.bidder_slug,
                    "modifier": self.publisher_bid_modifier.modifier,
                },
                {
                    "id": self.placement_bid_modifier.id,
                    "ad_group_id": self.ad_group.id,
                    "target": self.placement_bid_modifier.target,
                    "type": self.placement_bid_modifier.type,
                    "source": self.grouped_source.bidder_slug,
                    "modifier": self.placement_bid_modifier.modifier,
                },
            ],
            data,
        )
