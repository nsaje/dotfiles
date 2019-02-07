from django.test import TestCase

from . import serializers


class ExtraDataSerializerTest(TestCase):
    def setUp(self):
        self.deserialized = {
            "action_is_waiting": False,
            "can_archive": False,
            "can_restore": False,
            "default_settings": {
                "target_regions": [],
                "exclusion_target_regions": [],
                "target_devices": [],
                "target_os": [],
                "target_placements": [],
            },
            "retargetable_adgroups": [
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
        }
        self.serialized = {
            "action_is_waiting": False,
            "can_archive": False,
            "can_restore": False,
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
            "retargetable_adgroups": [
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
        }

    def test_serialization(self):
        serializer = serializers.ExtraDataSerializer(self.deserialized)
        self.assertEqual(serializer.data, self.serialized)
