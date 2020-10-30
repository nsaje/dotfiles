import json

from django.urls import reverse

import core.features.bid_modifiers
import core.features.bid_modifiers.constants
import dash.constants
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest


class BidModifiersTest(K1APIBaseTest):
    def setUp(self):
        self.source = magic_mixer.blend(core.models.Source, bidder_slug="test_source")
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
            type=(t for t in self.bid_modifier_types),
        )
        test_objs.append(
            magic_mixer.blend(
                core.features.bid_modifiers.BidModifier,
                source=self.source,
                source_slug=self.source.bidder_slug,
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

    # TODO: RTAP: remove after migration
    def test_realtime_autopilot_force_modifier(self):
        legacy_ad_group_no_agency = magic_mixer.blend(core.models.AdGroup, campaign__account__agency=None)
        legacy_ad_group_no_agency.campaign.settings.update_unsafe(None, autopilot=True)

        legacy_ad_group_no_flag = magic_mixer.blend(
            core.models.AdGroup, campaign__account__agency__uses_realtime_autopilot=False
        )
        legacy_ad_group_no_flag.campaign.settings.update_unsafe(None, autopilot=True)

        ad_group_no_autopilot = magic_mixer.blend(
            core.models.AdGroup, campaign__account__agency__uses_realtime_autopilot=True
        )
        ad_group_no_autopilot.campaign.settings.update_unsafe(None, autopilot=False)
        ad_group_no_autopilot.settings.update_unsafe(
            None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        ad_group_campaign_autopilot = magic_mixer.blend(
            core.models.AdGroup, campaign__account__agency__uses_realtime_autopilot=True
        )
        ad_group_campaign_autopilot.campaign.settings.update_unsafe(None, autopilot=True)
        ad_group_campaign_autopilot.settings.update_unsafe(
            None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        ad_group_realtime_autopilot = magic_mixer.blend(
            core.models.AdGroup, campaign__account__agency__uses_realtime_autopilot=True
        )
        ad_group_realtime_autopilot.campaign.settings.update_unsafe(None, autopilot=False)
        ad_group_realtime_autopilot.settings.update_unsafe(
            None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE
        )

        magic_mixer.cycle(5).blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=(
                ag
                for ag in (
                    legacy_ad_group_no_agency,
                    legacy_ad_group_no_flag,
                    ad_group_no_autopilot,
                    ad_group_campaign_autopilot,
                    ad_group_realtime_autopilot,
                )
            ),
            source=self.source,
            source_slug=self.source.bidder_slug,
            type=core.features.bid_modifiers.constants.BidModifierType.SOURCE,
            modifier=2.0,
        )
        magic_mixer.cycle(5).blend(
            core.features.bid_modifiers.BidModifier,
            ad_group=(
                ag
                for ag in (
                    legacy_ad_group_no_agency,
                    legacy_ad_group_no_flag,
                    ad_group_no_autopilot,
                    ad_group_campaign_autopilot,
                    ad_group_realtime_autopilot,
                )
            ),
            source=None,
            source_slug="",
            type=core.features.bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM,
            modifier=2.0,
        )

        response = self.client.get(
            reverse("k1api.bidmodifiers"),
            {
                "ad_group_ids": ",".join(
                    str(ag.id)
                    for ag in [
                        legacy_ad_group_no_agency,
                        legacy_ad_group_no_flag,
                        ad_group_no_autopilot,
                        ad_group_campaign_autopilot,
                        ad_group_realtime_autopilot,
                    ]
                )
            },
        )
        data = json.loads(response.content)

        self.assert_response_ok(response, data)
        self.assertEqual(10, len(data["response"]))

        for bm in data["response"]:
            if bm["type"] == core.features.bid_modifiers.constants.BidModifierType.SOURCE and bm["ad_group_id"] in [
                ad_group_campaign_autopilot.id,
                ad_group_realtime_autopilot.id,
            ]:
                self.assertEqual(1.0, bm["modifier"])
            else:
                self.assertEqual(2.0, bm["modifier"])
