from django.test import TestCase
from rest_framework.exceptions import ErrorDetail

import dash.models
from utils.magic_mixer import magic_mixer

from . import serializers


class SerializersTest(TestCase):
    def test_invalid_source_list(self):
        magic_mixer.blend(dash.models.Source, bidder_slug="a")
        data = [{"source": "a", "cpc": 0.5}, {"source": "b", "cpc": 0.6}]
        serializer = serializers.AdGroupSourceSerializer(data=data, many=True)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, ["Invalid source in object '{'source': 'b', 'cpc': 0.6}'!"])

    def test_num_queries(self):
        magic_mixer.blend(dash.models.Source, bidder_slug="a")
        magic_mixer.blend(dash.models.Source, bidder_slug="b")
        magic_mixer.blend(dash.models.Source, bidder_slug="c")
        magic_mixer.blend(dash.models.Source, bidder_slug="d")
        data = [
            {"source": "a", "cpc": 0.5},
            {"source": "b", "cpc": 0.6},
            {"source": "c", "cpc": 0.6},
            {"source": "d", "cpc": 0.6},
        ]
        with self.assertNumQueries(1):
            serializer = serializers.AdGroupSourceSerializer(data=data, many=True)
            self.assertTrue(serializer.is_valid())

    def test_invalid_many_input(self):
        magic_mixer.blend(dash.models.Source, bidder_slug="a")
        data = {"source": "a", "cpc": 0.5}  # data should be a list
        serializer = serializers.AdGroupSourceSerializer(data=data, many=True)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "non_field_errors": [
                    ErrorDetail(string='Expected a list of items but got type "dict".', code="not_a_list")
                ]
            },
        )

    def test_no_source(self):
        magic_mixer.blend(dash.models.Source, bidder_slug="a")
        data = [{"s": "a", "cpc": 0.5}]
        serializer = serializers.AdGroupSourceSerializer(data=data, many=True)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, ["Object '{'s': 'a', 'cpc': 0.5}' has no source!"])
