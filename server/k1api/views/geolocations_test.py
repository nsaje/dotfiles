import json
import logging

from django.urls import reverse

import dash.features.geolocation
import dash.features.ga
import dash.constants
import dash.models

from .base_test import K1APIBaseTest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GeolocationsTest(K1APIBaseTest):
    def setUp(self):
        self.locs = [
            {"key": "US", "name": "america", "outbrain_id": "abcdef", "woeid": "123"},
            {"key": "US-NY", "name": "new york", "outbrain_id": "bbcdef", "woeid": "124"},
        ]

        for loc in self.locs:
            dash.features.geolocation.Geolocation.objects.create(**loc)
        super(GeolocationsTest, self).setUp()

    def test_get_geolocations(self):
        response = self.client.get(
            reverse("k1api.geolocations"),
            {"keys": "US,US-NY,US:10000"},  # ZIPs can be ignored since we don't keep them all in DB
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        locations = data["response"]

        self.assertEqual(self.locs, locations)

    def test_get_geolocations_empty_keys(self):
        response = self.client.get(reverse("k1api.geolocations"), {"keys": ""})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        locations = data["response"]

        self.assertEqual([], locations)
