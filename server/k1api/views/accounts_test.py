import json

from django.urls import reverse

import dash.constants
import dash.features.ga
import dash.features.geolocation
import dash.models
from utils import zlogging
from utils.magic_mixer import magic_mixer
from utils.outbrain_marketer_helper import DEFUALT_OUTBRAIN_USER_EMAILS

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


class AccountMarketerViewTest(K1APIBaseTest):
    def setUp(self):
        super().setUp()
        self.current_marketer_id = "0058790e8fa99b8c1509749b97cb2278cd"
        self.current_marketer_version = 1
        self.account = magic_mixer.blend(
            dash.models.Account,
            outbrain_marketer_id=self.current_marketer_id,
            outbrain_marketer_version=self.current_marketer_version,
        )

    def test_reset_marketer_id(self):
        marketer_id = None

        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": self.account.id}),
            json.dumps({"current_outbrain_marketer_id": self.current_marketer_id, "outbrain_marketer_id": marketer_id}),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assert_response_ok(response, json_data)
        self.assertEqual(
            json_data["response"],
            {
                "id": self.account.id,
                "outbrain_marketer_id": marketer_id,
                "outbrain_marketer_version": self.current_marketer_version,
            },
        )
        account = dash.models.Account.objects.get(id=self.account.id)
        self.assertEqual(account.outbrain_marketer_id, marketer_id)
        self.assertEqual(account.outbrain_marketer_version, self.current_marketer_version)

    def test_change_marketer_id(self):
        marketer_name = f"Zemanta_{self.account.id}_{self.current_marketer_version + 1}"
        marketer_id = "0a587b0e8fa79b8c1309769b97ab22b8c2"

        ob_account_qs = dash.models.OutbrainAccount.objects.filter(marketer_id=marketer_id, marketer_name=marketer_name)
        self.assertFalse(ob_account_qs.exists())

        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": self.account.id}),
            json.dumps(
                {
                    "current_outbrain_marketer_id": self.current_marketer_id,
                    "outbrain_marketer_id": marketer_id,
                    "outbrain_marketer_name": marketer_name,
                }
            ),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assert_response_ok(response, json_data)
        self.assertEqual(
            json_data["response"],
            {
                "id": self.account.id,
                "outbrain_marketer_id": marketer_id,
                "outbrain_marketer_version": self.current_marketer_version + 1,
            },
        )
        account = dash.models.Account.objects.get(id=self.account.id)
        self.assertEqual(account.outbrain_marketer_id, marketer_id)
        self.assertEqual(account.outbrain_marketer_version, self.current_marketer_version + 1)

        self.assertEqual(ob_account_qs.count(), 1)
        self.assertTrue(ob_account_qs.first().used)

    def test_set_marketer_id(self):
        self.current_marketer_id = None
        self.account.outbrain_marketer_id = None
        self.account.save(None)

        marketer_name = f"Zemanta_{self.account.id}_{self.current_marketer_version + 1}"
        marketer_id = "0a587b0e8fa79b8c1309769b97ab22b8c2"

        ob_account_qs = dash.models.OutbrainAccount.objects.filter(marketer_id=marketer_id, marketer_name=marketer_name)
        self.assertFalse(ob_account_qs.exists())

        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": self.account.id}),
            json.dumps(
                {
                    "current_outbrain_marketer_id": self.current_marketer_id,
                    "outbrain_marketer_id": marketer_id,
                    "outbrain_marketer_name": marketer_name,
                }
            ),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assert_response_ok(response, json_data)
        self.assertEqual(
            json_data["response"],
            {
                "id": self.account.id,
                "outbrain_marketer_id": marketer_id,
                "outbrain_marketer_version": self.current_marketer_version + 1,
            },
        )
        account = dash.models.Account.objects.get(id=self.account.id)
        self.assertEqual(account.outbrain_marketer_id, marketer_id)
        self.assertEqual(account.outbrain_marketer_version, self.current_marketer_version + 1)

        self.assertEqual(ob_account_qs.count(), 1)
        self.assertTrue(ob_account_qs.first().used)

    def test_invalid_account_id(self):
        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": 0}),
            json.dumps({"current_outbrain_marketer_id": self.current_marketer_id, "outbrain_marketer_id": None}),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json_data, {"error": "Account does not exist", "response": None})

    def test_invalid_current_marketer_id(self):
        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": self.account.id}),
            json.dumps({"current_outbrain_marketer_id": "invalid_marketer_id", "outbrain_marketer_id": None}),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_data, {"error": "Invalid current Outbrain marketer id", "response": None})
        account = dash.models.Account.objects.get(id=self.account.id)
        self.assertEqual(account.outbrain_marketer_id, self.current_marketer_id)
        self.assertEqual(account.outbrain_marketer_version, self.current_marketer_version)

    def test_missing_argments(self):
        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": self.account.id}),
            json.dumps({}),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertTrue("error" in json_data)
        self.assertTrue("Missing attributes" in json_data["error"])
        self.assertTrue("current_outbrain_marketer_id" in json_data["error"])
        self.assertTrue("outbrain_marketer_id" in json_data["error"])
        account = dash.models.Account.objects.get(id=self.account.id)
        self.assertEqual(account.outbrain_marketer_id, self.current_marketer_id)
        self.assertEqual(account.outbrain_marketer_version, self.current_marketer_version)

    def test_missing_marketer_name(self):
        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": self.account.id}),
            json.dumps(
                {
                    "current_outbrain_marketer_id": self.current_marketer_id,
                    "outbrain_marketer_id": "0a587b0e8fa79b8c1309769b97ab22b8c2",
                }
            ),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_data, {"error": "Missing required outbrain_marketer_name attribute", "response": None})
        account = dash.models.Account.objects.get(id=self.account.id)
        self.assertEqual(account.outbrain_marketer_id, self.current_marketer_id)
        self.assertEqual(self.account.outbrain_marketer_version, self.current_marketer_version)

    def test_invalid_marketer_name(self):
        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": self.account.id}),
            json.dumps(
                {
                    "current_outbrain_marketer_id": self.current_marketer_id,
                    "outbrain_marketer_id": "0a587b0e8fa79b8c1309769b97ab22b8c2",
                    "outbrain_marketer_name": "invalid",
                }
            ),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_data, {"error": "Invalid format of outbrain_marketer_name", "response": None})
        account = dash.models.Account.objects.get(id=self.account.id)
        self.assertEqual(account.outbrain_marketer_id, self.current_marketer_id)
        self.assertEqual(self.account.outbrain_marketer_version, self.current_marketer_version)

    def test_invalid_marketer_name_account(self):
        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": self.account.id}),
            json.dumps(
                {
                    "current_outbrain_marketer_id": self.current_marketer_id,
                    "outbrain_marketer_id": "0a587b0e8fa79b8c1309769b97ab22b8c2",
                    "outbrain_marketer_name": f"Zemanta_0_{self.current_marketer_version + 1}",
                }
            ),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_data, {"error": "Account ID mismatch", "response": None})
        account = dash.models.Account.objects.get(id=self.account.id)
        self.assertEqual(account.outbrain_marketer_id, self.current_marketer_id)
        self.assertEqual(self.account.outbrain_marketer_version, self.current_marketer_version)

    def test_invalid_marketer_name_version(self):
        response = self.client.put(
            reverse("k1api.account_marketer", kwargs={"account_id": self.account.id}),
            json.dumps(
                {
                    "current_outbrain_marketer_id": self.current_marketer_id,
                    "outbrain_marketer_id": "0a587b0e8fa79b8c1309769b97ab22b8c2",
                    "outbrain_marketer_name": f"Zemanta_{self.account.id}_{self.current_marketer_version + 2}",
                }
            ),
            "application/json",
        )

        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_data, {"error": "Invalid Outbrain marketer version", "response": None})
        account = dash.models.Account.objects.get(id=self.account.id)
        self.assertEqual(account.outbrain_marketer_id, self.current_marketer_id)
        self.assertEqual(self.account.outbrain_marketer_version, self.current_marketer_version)


class AccountMarketerParametersViewTest(K1APIBaseTest):
    def setUp(self):
        super().setUp()
        self.non_cs_user_1 = magic_mixer.blend_user()
        self.non_cs_user_2 = magic_mixer.blend_user()
        self.cs_user_1 = magic_mixer.blend_user(permissions=["campaign_settings_cs_rep"])
        self.cs_user_2 = magic_mixer.blend_user(permissions=["campaign_settings_cs_rep"])

        self.non_ob_tag_1 = magic_mixer.blend(dash.models.EntityTag, name="some/tag")
        self.non_ob_tag_2 = magic_mixer.blend(dash.models.EntityTag, name="some/other/tag")
        self.ob_tag_1 = magic_mixer.blend(dash.models.EntityTag, name="account_type/performance/search")
        self.ob_tag_2 = magic_mixer.blend(dash.models.EntityTag, name="account_type/audiencedev/socagg")
        self.ob_tag_3 = magic_mixer.blend(dash.models.EntityTag, name="account_type/audiencedev/publisher")
        self.ob_tag_4 = magic_mixer.blend(dash.models.EntityTag, name="account_type/invalid/tag")

        self.account = magic_mixer.blend(
            dash.models.Account, outbrain_marketer_id="0a587b0e8fa79b8c1309769b97ab22b8c2", outbrain_marketer_version=3
        )
        self.account.entity_tags.add(self.non_ob_tag_1, self.non_ob_tag_2, self.ob_tag_1, self.ob_tag_2, self.ob_tag_4)

    def test_get_marketer_parameters(self):
        response = self.client.get(reverse("k1api.account_marketer_parameters", kwargs={"account_id": self.account.id}))

        json_data = json.loads(response.content)
        self.assert_response_ok(response, json_data)
        self.assertEqual(
            json_data["response"],
            {
                "id": self.account.id,
                "created_dt": self.account.created_dt.isoformat(),
                "outbrain_marketer_id": "0a587b0e8fa79b8c1309769b97ab22b8c2",
                "outbrain_marketer_version": 3,
                "outbrain_marketer_type": "ELASTIC_PUBLISHER",
                "content_classification": "PremiumElasticPublishers",
                "emails": [self.cs_user_1.email, self.cs_user_2.email] + DEFUALT_OUTBRAIN_USER_EMAILS,
            },
        )


class AccountsBulkMarketerParametersViewTest(K1APIBaseTest):
    def setUp(self):
        super().setUp()
        self.non_cs_user_1 = magic_mixer.blend_user()
        self.non_cs_user_2 = magic_mixer.blend_user()
        self.cs_user_1 = magic_mixer.blend_user(permissions=["campaign_settings_cs_rep"])
        self.cs_user_2 = magic_mixer.blend_user(permissions=["campaign_settings_cs_rep"])

        self.non_ob_tag_1 = magic_mixer.blend(dash.models.EntityTag, name="some/tag")
        self.non_ob_tag_2 = magic_mixer.blend(dash.models.EntityTag, name="some/other/tag")
        self.ob_tag_1 = magic_mixer.blend(dash.models.EntityTag, name="account_type/performance/search")
        self.ob_tag_2 = magic_mixer.blend(dash.models.EntityTag, name="account_type/audiencedev/socagg")
        self.ob_tag_3 = magic_mixer.blend(dash.models.EntityTag, name="account_type/audiencedev/publisher")
        self.ob_tag_4 = magic_mixer.blend(dash.models.EntityTag, name="account_type/invalid/tag")

        self.agency_a = magic_mixer.blend(dash.models.Agency)
        self.agency_b = magic_mixer.blend(dash.models.Agency)
        self.agency_c = magic_mixer.blend(dash.models.Agency)
        self.account_1 = magic_mixer.blend(dash.models.Account, outbrain_marketer_id="1", outbraion_marketer_version=1)
        self.account_2 = magic_mixer.blend(dash.models.Account, outbrain_marketer_id="2", outbraion_marketer_version=2)
        self.account_3 = magic_mixer.blend(dash.models.Account, outbrain_marketer_id="3", outbraion_marketer_version=3)
        self.account_4 = magic_mixer.blend(dash.models.Account, outbrain_marketer_id="4", outbraion_marketer_version=4)
        self.account_5 = magic_mixer.blend(dash.models.Account, outbrain_marketer_id="5", outbraion_marketer_version=5)
        self.account_6 = magic_mixer.blend(
            dash.models.Account, agency=self.agency_a, outbrain_marketer_id="6", outbraion_marketer_version=6
        )
        self.account_7 = magic_mixer.blend(
            dash.models.Account, agency=self.agency_a, outbrain_marketer_id="7", outbraion_marketer_version=7
        )
        self.account_8 = magic_mixer.blend(
            dash.models.Account, agency=self.agency_b, outbrain_marketer_id="8", outbraion_marketer_version=8
        )
        self.account_9 = magic_mixer.blend(
            dash.models.Account, agency=self.agency_c, outbrain_marketer_id="9", outbraion_marketer_version=9
        )
        self.account_1.entity_tags.add(self.non_ob_tag_1, self.ob_tag_1, self.ob_tag_2, self.ob_tag_4)
        self.account_2.entity_tags.add(self.non_ob_tag_2, self.ob_tag_3)
        self.account_3.entity_tags.add(self.non_ob_tag_2)
        self.agency_a.entity_tags.add(self.ob_tag_2)
        self.agency_b.entity_tags.add(self.ob_tag_3)
        self.agency_c.entity_tags.add(self.ob_tag_1)
        self.account_7.entity_tags.add(self.ob_tag_1)
        self.account_9.entity_tags.add(self.ob_tag_1)

        for a in (
            self.account_1,
            self.account_2,
            self.account_3,
            self.account_4,
            self.account_6,
            self.account_7,
            self.account_8,
            self.account_9,
        ):
            c = magic_mixer.blend(dash.models.Campaign, account=a)
            ag = magic_mixer.blend(dash.models.AdGroup, campaign=c)
            magic_mixer.blend(dash.models.AdGroupSource, ad_group=ag, source__id=3)

    def test_get_bulk_marketer_parameters(self):
        account_ids = ",".join(
            str(i)
            for i in [
                self.account_1.id,
                self.account_2.id,
                self.account_3.id,
                self.account_4.id,
                self.account_5.id,
                self.account_6.id,
                self.account_7.id,
                self.account_8.id,
                self.account_9.id,
            ]
        )

        # 1 query related to replica, 2 queries due to permissions checks, 1 for accounts, 1 for entity tags
        with self.assertNumQueries(6):
            response = self.client.get(
                reverse("k1api.accounts_bulk_marketer_parameters") + f"?account_ids={account_ids}"
            )

        json_data = json.loads(response.content)
        self.assert_response_ok(response, json_data)
        self.assertEqual(
            json_data["response"],
            {
                "accounts": [
                    {
                        "id": self.account_1.id,
                        "created_dt": self.account_1.created_dt.isoformat(),
                        "outbrain_marketer_id": self.account_1.outbrain_marketer_id,
                        "outbrain_marketer_version": self.account_1.outbrain_marketer_version,
                        "outbrain_marketer_type": "ELASTIC_PUBLISHER",
                        "content_classification": "PremiumElasticPublishers",
                    },
                    {
                        "id": self.account_2.id,
                        "created_dt": self.account_2.created_dt.isoformat(),
                        "outbrain_marketer_id": self.account_2.outbrain_marketer_id,
                        "outbrain_marketer_version": self.account_2.outbrain_marketer_version,
                        "outbrain_marketer_type": "AFFILIATES_AND_SMB",
                        "content_classification": "AdvertorialOther",
                    },
                    {
                        "id": self.account_3.id,
                        "created_dt": self.account_3.created_dt.isoformat(),
                        "outbrain_marketer_id": self.account_3.outbrain_marketer_id,
                        "outbrain_marketer_version": self.account_3.outbrain_marketer_version,
                        "outbrain_marketer_type": "AFFILIATES_AND_SMB",
                        "content_classification": "AdvertorialOther",
                    },
                    {
                        "id": self.account_4.id,
                        "created_dt": self.account_4.created_dt.isoformat(),
                        "outbrain_marketer_id": self.account_4.outbrain_marketer_id,
                        "outbrain_marketer_version": self.account_4.outbrain_marketer_version,
                        "outbrain_marketer_type": "AFFILIATES_AND_SMB",
                        "content_classification": "AdvertorialOther",
                    },
                    {
                        "id": self.account_6.id,
                        "created_dt": self.account_6.created_dt.isoformat(),
                        "outbrain_marketer_id": self.account_6.outbrain_marketer_id,
                        "outbrain_marketer_version": self.account_6.outbrain_marketer_version,
                        "outbrain_marketer_type": "ELASTIC_PUBLISHER",
                        "content_classification": "PremiumElasticPublishers",
                    },
                    {
                        "id": self.account_7.id,
                        "created_dt": self.account_7.created_dt.isoformat(),
                        "outbrain_marketer_id": self.account_7.outbrain_marketer_id,
                        "outbrain_marketer_version": self.account_7.outbrain_marketer_version,
                        "outbrain_marketer_type": "SEARCH",
                        "content_classification": "SERP",
                    },
                    {
                        "id": self.account_8.id,
                        "created_dt": self.account_8.created_dt.isoformat(),
                        "outbrain_marketer_id": self.account_8.outbrain_marketer_id,
                        "outbrain_marketer_version": self.account_8.outbrain_marketer_version,
                        "outbrain_marketer_type": "AFFILIATES_AND_SMB",
                        "content_classification": "AdvertorialOther",
                    },
                    {
                        "id": self.account_9.id,
                        "created_dt": self.account_9.created_dt.isoformat(),
                        "outbrain_marketer_id": self.account_9.outbrain_marketer_id,
                        "outbrain_marketer_version": self.account_9.outbrain_marketer_version,
                        "outbrain_marketer_type": "SEARCH",
                        "content_classification": "SERP",
                    },
                ],
                "emails": [self.cs_user_1.email, self.cs_user_2.email] + DEFUALT_OUTBRAIN_USER_EMAILS,
            },
        )
