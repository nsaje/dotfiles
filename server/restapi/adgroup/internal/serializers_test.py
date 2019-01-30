from django.test import TestCase

from . import serializers


class ExtraDataSerializerTest(TestCase):
    def test_serialization(self):
        data = {
            "action_is_waiting": False,
            "can_archive": False,
            "can_restore": False,
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
        serializer = serializers.ExtraDataSerializer(data)
        self.assertEqual(serializer.data, data)
