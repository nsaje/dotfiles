import json
import logging

from django.urls import reverse

import dash.models
from utils import zlogging

from .base_test import K1APIBaseTest

logger = zlogging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SourcesTest(K1APIBaseTest):
    def test_get_default_source_credentials(self):
        response = self.client.get(reverse("k1api.sources"), {"source_slugs": "facebook"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        data = data["response"]
        self.assertEqual(data[0]["credentials"]["credentials"], "h")

    def test_get_source_credentials(self):
        test_cases = [["adblade"], ["adblade", "outbrain", "yahoo"]]
        for source_types in test_cases:
            self._test_source_credentials_filter(source_types)

    def _test_source_credentials_filter(self, source_slugs=None):
        response = self.client.get(reverse("k1api.sources"), {"source_slugs": ",".join(source_slugs)})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        for source in data:
            sc = dash.models.SourceCredentials.objects.get(pk=source["credentials"]["id"])
            self.assertEqual(sc.credentials, source["credentials"]["credentials"])

        scs = dash.models.Source.objects.all()
        if source_slugs:
            scs = scs.filter(bidder_slug__in=source_slugs)
        self.assertEqual(len(data), scs.count())

    def test_get_sources_by_tracking_slug(self):
        response = self.client.get(reverse("k1api.sources"))

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertGreater(len(data), 0)
        for source in data:
            self.assertIn("id", source)
