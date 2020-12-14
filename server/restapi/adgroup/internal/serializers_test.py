from django.test import TestCase

import core.models
import dash.constants
from core.features import bid_modifiers
from utils.magic_mixer import magic_mixer

from . import serializers


class ExtraDataSerializerTestCase(TestCase):
    def setUp(self):
        self.deserialized = {
            "action_is_waiting": False,
            "can_restore": False,
            "is_campaign_autopilot_enabled": False,
            "account_id": 12345,
            "agency_id": 12345,
            "agency_uses_realtime_autopilot": False,
            "currency": dash.constants.Currency.USD,
            "optimization_objective": dash.constants.CampaignGoalKPI.CPC,
            "default_settings": {
                "target_regions": [],
                "exclusion_target_regions": [],
                "target_devices": [],
                "target_os": [],
                "target_environments": [],
            },
            "retargetable_ad_groups": [
                {"id": 795, "name": "Pre-launch (desktop)", "campaign_name": "Plugin Magazin", "archived": False}
            ],
            "audiences": [{"id": 698, "name": "phase 1", "archived": False}],
            "warnings": {"retargeting": {"sources": ["AdZerk", "Rubicon Display"]}},
            "hacks": [
                {
                    "confirmed": True,
                    "details": "Adding pixel https://p1.zemanta.com/p/489/3176/ as impression tracker on all RCS ads.",
                    "level": "Global",
                    "source": "RCS",
                    "summary": "Implement pixel on all the ads",
                }
            ],
            "deals": [
                {
                    "level": "Global",
                    "direct_deal_connection_id": 1234,
                    "deal_id": "1234_ABC",
                    "source": "SOURCE",
                    "exclusive": True,
                    "description": "DEAL FOR SOURCE",
                    "is_applied": True,
                }
            ],
            "bid_modifier_type_summaries": [
                {"type": bid_modifiers.constants.BidModifierType.DEVICE, "count": 7, "min": 0.85, "max": 1.2},
                {"type": bid_modifiers.constants.BidModifierType.STATE, "count": 3, "min": 0.9, "max": 1.1},
            ],
            "current_bids": {"cpc": "0.4500", "cpm": "1.0000"},
        }
        self.serialized = {
            "action_is_waiting": False,
            "can_restore": False,
            "is_campaign_autopilot_enabled": False,
            "account_id": "12345",
            "agency_id": "12345",
            "agency_uses_realtime_autopilot": False,
            "currency": dash.constants.Currency.USD,
            "optimization_objective": dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.CPC),
            "default_settings": {
                "target_regions": {"countries": [], "regions": [], "dma": [], "cities": [], "postal_codes": []},
                "exclusion_target_regions": {
                    "countries": [],
                    "regions": [],
                    "dma": [],
                    "cities": [],
                    "postal_codes": [],
                },
                "target_devices": [],
                "target_os": [],
                "target_environments": [],
            },
            "retargetable_ad_groups": [
                {"id": "795", "name": "Pre-launch (desktop)", "campaign_name": "Plugin Magazin", "archived": False}
            ],
            "audiences": [{"id": "698", "name": "phase 1", "archived": False}],
            "warnings": {"retargeting": {"sources": ["AdZerk", "Rubicon Display"]}},
            "hacks": [
                {
                    "confirmed": True,
                    "details": "Adding pixel https://p1.zemanta.com/p/489/3176/ as impression tracker on all RCS ads.",
                    "level": "Global",
                    "source": "RCS",
                    "summary": "Implement pixel on all the ads",
                }
            ],
            "deals": [
                {
                    "level": "Global",
                    "direct_deal_connection_id": "1234",
                    "deal_id": "1234_ABC",
                    "source": "SOURCE",
                    "exclusive": True,
                    "description": "DEAL FOR SOURCE",
                    "is_applied": True,
                }
            ],
            "bid_modifier_type_summaries": [
                {
                    "type": bid_modifiers.constants.BidModifierType.get_name(
                        bid_modifiers.constants.BidModifierType.DEVICE
                    ),
                    "count": 7,
                    "min": 0.85,
                    "max": 1.2,
                },
                {
                    "type": bid_modifiers.constants.BidModifierType.get_name(
                        bid_modifiers.constants.BidModifierType.STATE
                    ),
                    "count": 3,
                    "min": 0.9,
                    "max": 1.1,
                },
            ],
            "current_bids": {"cpc": "0.4500", "cpm": "1.0000"},
        }

    def test_serialization(self):
        serializer = serializers.ExtraDataSerializer(self.deserialized)
        self.assertEqual(serializer.data, self.serialized)


class CloneAdGroupSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.account = magic_mixer.blend(core.models.Account)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.content_ads = magic_mixer.cycle(5).blend(core.models.ContentAd, ad_group=self.ad_group, archived=False)
        self.dest_campaign = magic_mixer.blend(core.models.Campaign, account=self.account)

    def test_valid(self):
        serializer = serializers.CloneAdGroupSerializer(
            data={
                "ad_group_id": self.ad_group.pk,
                "destination_campaign_id": self.dest_campaign.pk,
                "destination_ad_group_name": "Test",
                "clone_ads": True,
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_name_too_long(self):
        serializer = serializers.CloneAdGroupSerializer(
            data={
                "ad_group_id": self.ad_group.pk,
                "destination_campaign_id": self.dest_campaign.pk,
                "destination_ad_group_name": 260 * "x",
                "clone_ads": True,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(
            serializer.errors, {"destination_ad_group_name": ["Ensure this field has no more than 256 characters."]}
        )
