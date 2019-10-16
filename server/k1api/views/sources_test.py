import json

import mock
from django.urls import reverse

import dash.models
import structlog

from .base_test import K1APIBaseTest

logger = structlog.get_logger(__name__)
logger.setLevel(structlog.stdlib.INFO)


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

    @mock.patch("utils.redirector_helper.upsert_audience")
    def test_update_source_pixel_with_existing(self, redirector_mock):
        body = {
            "pixel_id": 1,
            "source_type": "facebook",
            "url": "http://www.dummy_fb.com/pixie_endpoint",
            "source_pixel_id": "fb_dummy_id",
        }
        response = self.client.put(reverse("k1api.source_pixels"), json.dumps(body), "application/json")

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertDictEqual(body, data["response"])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=3)
        self.assertEqual(updated_pixel.url, "http://www.dummy_fb.com/pixie_endpoint")
        self.assertEqual(updated_pixel.source_pixel_id, "fb_dummy_id")

        audience = dash.models.Audience.objects.get(pixel_id=1)
        redirector_mock.assert_called_once_with(audience)

    @mock.patch("utils.redirector_helper.upsert_audience")
    def test_update_source_pixel_with_existing_for_outbrain(self, redirector_mock):
        body = {
            "pixel_id": 2,
            "source_type": "outbrain",
            "url": "http://www.dummy_ob.com/pixie_endpoint",
            "source_pixel_id": "ob_dummy_id",
        }
        response = self.client.put(reverse("k1api.source_pixels"), json.dumps(body), "application/json")

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertDictEqual(body, data["response"])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=1)
        self.assertEqual(updated_pixel.pixel.id, 2)

        audiences = dash.models.Audience.objects.filter(pixel_id__in=[2, 1])
        redirector_mock.assert_has_calls([mock.call(audiences[0]), mock.call(audiences[1])], any_order=True)

    @mock.patch("utils.redirector_helper.upsert_audience")
    def test_update_source_pixel_create_new(self, redirector_mock):
        body = {
            "pixel_id": 3,
            "source_type": "facebook",
            "url": "http://www.dummy_fb.com/pixie_endpoint",
            "source_pixel_id": "fb_dummy_id",
        }
        response = self.client.put(reverse("k1api.source_pixels"), json.dumps(body), "application/json")

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertDictEqual(body, data["response"])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=7)
        self.assertEqual(updated_pixel.url, "http://www.dummy_fb.com/pixie_endpoint")
        self.assertEqual(updated_pixel.source_pixel_id, "fb_dummy_id")

        self.assertFalse(redirector_mock.called)

    @mock.patch("utils.redirector_helper.upsert_audience")
    def test_update_source_pixel_create_new_for_outbrain(self, redirector_mock):
        body = {
            "pixel_id": 3,
            "source_type": "outbrain",
            "url": "http://www.dummy_ob.com/pixie_endpoint",
            "source_pixel_id": "ob_dummy_id",
        }
        response = self.client.put(reverse("k1api.source_pixels"), json.dumps(body), "application/json")

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertDictEqual(body, data["response"])

        updated_pixel = dash.models.SourceTypePixel.objects.get(pk=8)
        self.assertEqual(updated_pixel.url, "http://www.dummy_ob.com/pixie_endpoint")
        self.assertEqual(updated_pixel.source_pixel_id, "ob_dummy_id")

        self.assertFalse(redirector_mock.called)
