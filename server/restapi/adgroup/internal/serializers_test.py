from django.test import TestCase

import dash.constants
from core.features import bid_modifiers

from . import serializers


class ExtraDataSerializerTest(TestCase):
    def setUp(self):
        self.deserialized = {
            "action_is_waiting": False,
            "can_archive": False,
            "can_restore": False,
            "is_campaign_autopilot_enabled": False,
            "account_id": 12345,
            "currency": dash.constants.Currency.USD,
            "optimization_objective": dash.constants.CampaignGoalKPI.CPC,
            "default_settings": {
                "target_regions": [],
                "exclusion_target_regions": [],
                "target_devices": [],
                "target_os": [],
                "target_placements": [],
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
        }
        self.serialized = {
            "action_is_waiting": False,
            "can_archive": False,
            "can_restore": False,
            "is_campaign_autopilot_enabled": False,
            "account_id": "12345",
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
                "target_placements": [],
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
        }

    def test_serialization(self):
        serializer = serializers.ExtraDataSerializer(self.deserialized)
        self.assertEqual(serializer.data, self.serialized)
