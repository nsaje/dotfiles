from django.test import TestCase

from . import hack


class HackSerializer(TestCase):
    def test_serialization(self):
        data = {
            "summary": "test summary 1",
            "source": "test source 1",
            "level": "test level 1",
            "details": "test details 1",
            "confirmed": True,
        }
        serializer = hack.HackSerializer(data)
        self.assertEqual(serializer.data, data)
