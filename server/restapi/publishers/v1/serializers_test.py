from django.test import TestCase

import core.models
from restapi.publishers.v1 import serializers
from utils.magic_mixer import magic_mixer


class Test(TestCase):
    def test_list(self):
        source = magic_mixer.blend(core.models.Source, bidder_slug="mysource")
        data = [
            {"name": "test", "source": "mysource", "status": "BLACKLISTED", "level": "ADGROUP"},
            {"name": "test2", "source": None, "status": "BLACKLISTED", "level": "ADGROUP"},
        ]
        serializer = serializers.PublisherSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        expected_data = [
            {"name": "test", "source": source, "status": 2, "level": "adgroup"},
            {"name": "test2", "source": None, "status": 2, "level": "adgroup"},
        ]
        self.assertEqual(expected_data, serializer.validated_data)
