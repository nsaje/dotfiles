import datetime

from secretcrypt import Secret

import apt.common
import dash.constants

from ..base.test_case import APTTestCase

AGENCY_MANAGER_ID = 5463  # agency-manager@apt-test.com

API_CALL_RETRIES = 5
API_URL = "https://one.zemanta.com/"


class CreateEntityAPTTestCase(APTTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        CLIENT_ID = (
            Secret(
                "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QHERac7pq7MpmYpDOi+7o6UAAAAhzCBhAYJKoZIhvcNAQcGoHcwdQIBADBwBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDCtQ15C0QlmVqDGpngIBEIBDb8CeJ2dcy46gErCj7V6UdB1rZILUeoiScunztlCyJua4DolFD/HOzPcKBUVpsfoDHRB+lEC+f+XStlK0zboJ6a1zbA=="
            )
            .get()
            .decode("utf-8")
        )
        CLIENT_SECRET = (
            Secret(
                "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QH6750mDcHn6k3JMu/hcspXAAAA4zCB4AYJKoZIhvcNAQcGoIHSMIHPAgEAMIHJBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDKz44TKrZ0HsioqLYwIBEICBm773rka9so8b8tj7upzGrFCJfcMctypc17g/e4YUulrOxlx4dkapug+cQdlu9mwJ3Ae4nC1+iIle3+EV5uNHmuyXs6rwDuO/lZq7cVsagHfJHDKUYxWzKnsyFOg7JAdEdW48omsUvesZvtiAg/T/YJJbH7pcRYn28n2KDv2sh8EMqqqwzJ3NhgrPsItBSoPXQXEQUluygQA+VSRj"
            )
            .get()
            .decode("utf-8")
        )

        cls.client = apt.common.Z1Client(CLIENT_ID, CLIENT_SECRET)
        cls.account_id = None
        cls.campaign_id = None
        cls.adgroup_id = None

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        if cls.adgroup_id:
            cls._archive_entity("adgroups", cls.adgroup_id)

        if cls.campaign_id:
            cls._archive_entity("campaigns", cls.campaign_id)

        if cls.account_id:
            cls._archive_entity("accounts", cls.account_id)

    @classmethod
    def _archive_entity(cls, entity, entity_id):
        for i in range(0, API_CALL_RETRIES):
            response = cls.client.make_api_call(
                API_URL + "rest/internal/{}/{}".format(entity, entity_id), method="PUT", data={"archived": True}
            )
            if response.status_code == 200:
                break

    def _create_account(self):
        response = self.client.make_api_call(API_URL + "rest/internal/accounts/defaults/", method="GET")
        post_data = response.json()["data"].copy()
        post_data["name"] = "APT Test Account {}".format(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
        post_data["currency"] = dash.constants.Currency.get_name(dash.constants.Currency.USD)

        response = self.client.make_api_call(API_URL + "rest/internal/accounts/", data=post_data)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()

        account_id = response_json["data"]["id"]
        self.__class__.account_id = account_id

        self.assertIsNotNone(account_id)
        self.assertEqual(response_json["data"]["name"], post_data["name"])

    def _create_campaign(self):
        self.assertIsNotNone(self.account_id)

        response = self.client.make_api_call(
            API_URL + "rest/internal/campaigns/defaults/?accountId={}".format(self.account_id), method="GET"
        )

        post_data = response.json()["data"].copy()
        post_data["accountId"] = self.account_id
        post_data["name"] = "APT Test Campaign {}".format(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
        post_data["iabCategory"] = dash.constants.IABCategory.get_name(dash.constants.IABCategory.IAB1_1)
        post_data["goals"] = [
            {
                "conversionGoal": None,
                "id": None,
                "primary": True,
                "type": dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.TIME_ON_SITE),
                "value": "30.00",
            }
        ]

        response = self.client.make_api_call(API_URL + "rest/internal/campaigns/", data=post_data)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()

        campaign_id = response_json["data"]["id"]
        self.__class__.campaign_id = campaign_id

        self.assertIsNotNone(campaign_id)
        self.assertEqual(response_json["data"]["name"], post_data["name"])

    def _create_adgroup(self):
        self.assertIsNotNone(self.campaign_id)

        response = self.client.make_api_call(
            API_URL + "rest/internal/adgroups/defaults/?campaignId={}".format(self.campaign_id), method="GET"
        )

        post_data = response.json()["data"].copy()
        post_data["campaignId"] = self.campaign_id
        post_data["name"] = "APT Test Ad Group {}".format(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

        response = self.client.make_api_call(API_URL + "rest/internal/adgroups/", data=post_data)
        self.assertEqual(response.status_code, 201)
        response_json = response.json()

        adgroup_id = response_json["data"]["id"]
        self.__class__.adgroup_id = adgroup_id

        self.assertIsNotNone(adgroup_id)
        self.assertEqual(response_json["data"]["name"], post_data["name"])

    def _create_content_ad(self):
        batch_post_data = [
            {
                "label": "My label",
                "url": "http://example.com/",
                "title": "APT Test Content Ad {}".format(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
                "imageUrl": "http://example.com/image",
                "imageCrop": "faces",
                "displayUrl": "http://example.com/",
                "brandName": "APT Test Company",
                "description": "APT Test Description",
                "callToAction": "Read more",
                "trackerUrls": ["https://example.com/t1"],
            }
        ]
        response = self.client.make_api_call(
            API_URL + "rest/v1/contentads/batch/?adGroupId={}".format(self.adgroup_id), data=batch_post_data
        )
        self.assertEqual(response.status_code, 201)
        batch_data = response.json()["data"].copy()

        response = self.client.make_api_call(
            API_URL + "rest/v1/contentads/batch/{}".format(batch_data["id"]), method="GET"
        )
        self.assertEqual(response.status_code, 200)

    def test_create_entity_flow(self):
        self._create_account()
        self._create_campaign()
        self._create_adgroup()
        self._create_content_ad()
