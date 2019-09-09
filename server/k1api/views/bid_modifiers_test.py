import json

from django.urls import reverse

import core.features.bid_modifiers
import core.features.bid_modifiers.constants
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest


class BidModifiersTest(K1APIBaseTest):
    def setUp(self):
        self.source = magic_mixer.blend(core.models.Source, bidder_slug="test_source")
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
        test_objs = magic_mixer.cycle(3).blend(core.features.bid_modifiers.BidModifier, source=None, source_slug="")
        test_objs.append(
            magic_mixer.blend(
                core.features.bid_modifiers.BidModifier, source=self.source, source_slug=self.source.bidder_slug
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
            type=core.features.bid_modifiers.constants.BidModifierType.AD,
        )
        response = self.client.get(reverse("k1api.bidmodifiers"), {"marker": test_objs[2].id, "limit": 5})
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(data["response"], [self.repr(obj) for obj in test_objs[3:8]])

    def test_filter_by_type(self):
        all_types = list(core.features.bid_modifiers.BidModifierType.get_all())
        test_objs = magic_mixer.cycle(len(all_types)).blend(
            core.features.bid_modifiers.BidModifier, type=(typ for typ in all_types)
        )
        ad_type = core.features.bid_modifiers.BidModifierType.AD
        response = self.client.get(reverse("k1api.bidmodifiers"), {"type": ad_type})
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(1, len(data["response"]))
        self.assertEqual(data["response"], [self.repr(obj) for obj in test_objs if obj.type == ad_type])
