import json

from django.urls import reverse

import dash.constants
import dash.features.ga
import dash.features.geolocation
import dash.models
from utils import zlogging
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest

logger = zlogging.getLogger(__name__)
logger.setLevel(zlogging.INFO)


class AccountsTest(K1APIBaseTest):
    def test_get_accounts(self):
        response = self.client.get(reverse("k1api.accounts"))
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]
        self.assertEqual(len(data), dash.models.Account.objects.count())

    def test_get_accounts_with_id(self):
        response = self.client.get(reverse("k1api.accounts"), {"account_ids": 1})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 1)
        self.assertEqual(
            data[0],
            {
                "id": 1,
                "agency_id": 20,
                "name": "test account 1",
                "outbrain_marketer_id": "abcde",
                "outbrain_amplify_review_only": False,
                "default_cs_representative": "superuser@test.com",
                "custom_audiences": [
                    {
                        "pixel_id": 1,
                        "rules": [{"type": 1, "values": "dummy", "id": 1}, {"type": 2, "values": "dummy2", "id": 2}],
                        "name": "Audience 1",
                        "id": 1,
                        "ttl": 90,
                        "prefill_days": 180,
                    },
                    {
                        "pixel_id": 2,
                        "rules": [{"type": 1, "values": "dummy3", "id": 3}, {"type": 2, "values": "dummy4", "id": 4}],
                        "name": "Audience 2",
                        "id": 2,
                        "ttl": 60,
                        "prefill_days": 180,
                    },
                ],
                "pixels": [
                    {
                        "id": 1,
                        "name": "Pixel 1",
                        "slug": "testslug1",
                        "audience_enabled": False,
                        "additional_pixel": False,
                        "source_pixels": [
                            {
                                "url": "http://www.ob.com/pixelendpoint",
                                "source_pixel_id": "ob_zem1",
                                "source_type": "outbrain",
                            },
                            {
                                "url": "http://www.y.com/pixelendpoint",
                                "source_pixel_id": "y_zem1",
                                "source_type": "yahoo",
                            },
                            {
                                "url": "http://www.fb.com/pixelendpoint",
                                "source_pixel_id": "fb_zem1",
                                "source_type": "facebook",
                            },
                        ],
                    },
                    {
                        "id": 2,
                        "name": "Pixel 2",
                        "slug": "testslug2",
                        "audience_enabled": True,
                        "additional_pixel": False,
                        "source_pixels": [
                            {
                                "url": "http://www.xy.com/pixelendpoint",
                                "source_pixel_id": "xy_zem2",
                                "source_type": "taboola",
                            },
                            {
                                "url": "http://www.y.com/pixelendpoint",
                                "source_pixel_id": "y_zem2",
                                "source_type": "yahoo",
                            },
                            {
                                "url": "http://www.fb.com/pixelendpoint",
                                "source_pixel_id": "fb_zem2",
                                "source_type": "facebook",
                            },
                        ],
                    },
                ],
            },
        )

    def test_get_custom_audience(self):
        response = self.client.get(reverse("k1api.accounts"), {"account_ids": 1})

        json_data = json.loads(response.content)
        self.assert_response_ok(response, json_data)
        accounts_data = json_data["response"]
        self.assertEqual(1, len(accounts_data))
        data = accounts_data[0]["custom_audiences"]

        self.assertEqual(2, len(data))
        self.assertEqual(
            data,
            [
                {
                    "id": 1,
                    "name": "Audience 1",
                    "pixel_id": 1,
                    "rules": [{"id": 1, "type": 1, "values": "dummy"}, {"id": 2, "type": 2, "values": "dummy2"}],
                    "ttl": 90,
                    "prefill_days": 180,
                },
                {
                    "id": 2,
                    "name": "Audience 2",
                    "pixel_id": 2,
                    "rules": [{"id": 3, "type": 1, "values": "dummy3"}, {"id": 4, "type": 2, "values": "dummy4"}],
                    "ttl": 60,
                    "prefill_days": 180,
                },
            ],
        )


class AccountMarketerIdViewTest(K1APIBaseTest):
    def setUp(self):
        super().setUp()
        self.current_marketer_id = "0058790e8fa99b8c1509749b97cb2278cd"
        self.account = magic_mixer.blend(dash.models.Account, outbrain_marketer_id=self.current_marketer_id)

    def test_change_marketer_id(self):
        self._set_and_assert_marketer_id(self.current_marketer_id, "0a587b0e8fa79b8c1309769b97ab22b8c2")

    def test_set_marketer_id(self):
        self.current_marketer_id = None
        self.account.outbrain_marketer_id = None
        self.account.save(None)
        self._set_and_assert_marketer_id(self.current_marketer_id, "0a587b0e8fa79b8c1309769b97ab22b8c2")

    def test_reset_marketer_id(self):
        self._set_and_assert_marketer_id(self.current_marketer_id, None)

    def _set_and_assert_marketer_id(self, current_marketer_id, marketer_id):
        response = self.client.put(
            reverse("k1api.account_marketer_id", kwargs={"account_id": self.account.id}),
            json.dumps({"current_outbrain_marketer_id": current_marketer_id, "outbrain_marketer_id": marketer_id}),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assert_response_ok(response, json_data)
        self.assertEqual(json_data["response"], {"id": self.account.id, "outbrain_marketer_id": marketer_id})
        self.assertEqual(dash.models.Account.objects.get(id=self.account.id).outbrain_marketer_id, marketer_id)

    def test_invalid_account_id(self):
        response = self.client.put(
            reverse("k1api.account_marketer_id", kwargs={"account_id": 0}),
            json.dumps({"current_outbrain_marketer_id": self.current_marketer_id, "outbrain_marketer_id": None}),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json_data, {"error": "Account does not exist", "response": None})

    def test_invalid_current_marketer_id(self):
        response = self.client.put(
            reverse("k1api.account_marketer_id", kwargs={"account_id": self.account.id}),
            json.dumps({"current_outbrain_marketer_id": "invalid_marketer_id", "outbrain_marketer_id": None}),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_data, {"error": "Invalid current Outbrain marketer id", "response": None})
        self.assertEqual(
            dash.models.Account.objects.get(id=self.account.id).outbrain_marketer_id, self.current_marketer_id
        )
