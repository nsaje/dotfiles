import datetime
import json
import urllib.error
import urllib.parse
import urllib.request

import structlog
from django.urls import reverse

import dash.constants
import dash.features.ga
import dash.features.geolocation
import dash.models

from .base_test import K1APIBaseTest

logger = structlog.get_logger(__name__)
logger.setLevel(structlog.stdlib.INFO)


class GAAccountsTest(K1APIBaseTest):
    def test_get_ga_accounts(self):
        dash.features.ga.GALinkedAccounts.objects.create(
            customer_ga_account_id="124", zem_ga_account_email="a1@gapps.com", has_read_and_analyze=True
        )

        response = self.client.get(reverse("k1api.ga_accounts"))

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]["account_id"], 1)
        self.assertEqual(data[0]["ga_account_id"], "123")
        self.assertEqual(data[0]["ga_web_property_id"], "UA-123-2")
        self.assertEqual(data[0]["service_email"], None)
        self.assertEqual(data[1]["account_id"], 2)
        self.assertEqual(data[1]["ga_account_id"], "124")
        self.assertEqual(data[1]["ga_web_property_id"], "UA-124-3")
        self.assertEqual(data[1]["service_email"], "a1@gapps.com")
        self.assertEqual(data[2]["account_id"], 3)
        self.assertEqual(data[2]["ga_account_id"], None)
        self.assertEqual(data[2]["ga_web_property_id"], None)
        self.assertEqual(data[2]["service_email"], None)
        self.assertEqual(data[3]["account_id"], 1000)
        self.assertEqual(data[3]["ga_account_id"], None)
        self.assertEqual(data[3]["ga_web_property_id"], None)
        self.assertEqual(data[3]["service_email"], None)

    def test_get_ga_accounts_since_ever(self):
        dash.features.ga.GALinkedAccounts.objects.create(
            customer_ga_account_id="124", zem_ga_account_email="a1@gapps.com", has_read_and_analyze=True
        )

        campaign_settings = dash.models.Campaign.objects.get(pk=1).get_current_settings().copy_settings()
        campaign_settings.ga_property_id = "UA-123-4"
        campaign_settings.save(None)

        response = self.client.get(
            reverse("k1api.ga_accounts"), QUERY_STRING=urllib.parse.urlencode({"date_since": "2014-07-01"})
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 7)
        self.assertEqual(
            data,
            [
                {"ga_web_property_id": "UA-123-2", "account_id": 1, "ga_account_id": "123", "service_email": None},
                {"ga_web_property_id": "UA-123-4", "account_id": 1, "ga_account_id": "123", "service_email": None},
                {
                    "ga_web_property_id": "UA-124-0",
                    "account_id": 2,
                    "ga_account_id": "124",
                    "service_email": "a1@gapps.com",
                },
                {
                    "ga_web_property_id": "UA-124-1",
                    "account_id": 2,
                    "ga_account_id": "124",
                    "service_email": "a1@gapps.com",
                },
                {
                    "ga_web_property_id": "UA-124-3",
                    "account_id": 2,
                    "ga_account_id": "124",
                    "service_email": "a1@gapps.com",
                },
                {"ga_web_property_id": None, "account_id": 3, "ga_account_id": None, "service_email": None},
                {"ga_web_property_id": None, "account_id": 1000, "ga_account_id": None, "service_email": None},
            ],
        )

    def test_get_ga_accounts_since_yesterday(self):
        self.campaign.settings.update(None, ga_property_id="UA-123-4")

        response = self.client.get(
            reverse("k1api.ga_accounts"),
            QUERY_STRING=urllib.parse.urlencode({"date_since": str(datetime.date.today() - datetime.timedelta(1))}),
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 5)
        self.assertEqual(data[0]["account_id"], 1)
        self.assertEqual(data[0]["ga_account_id"], "123")
        self.assertEqual(data[0]["ga_web_property_id"], "UA-123-2")
        self.assertEqual(data[0]["service_email"], None)
        self.assertEqual(data[1]["account_id"], 1)
        self.assertEqual(data[1]["ga_account_id"], "123")
        self.assertEqual(data[1]["ga_web_property_id"], "UA-123-4")
        self.assertEqual(data[1]["service_email"], None)
        self.assertEqual(data[2]["account_id"], 2)
        self.assertEqual(data[2]["ga_account_id"], "124")
        self.assertEqual(data[2]["ga_web_property_id"], "UA-124-3")
        self.assertEqual(data[2]["service_email"], None)
        self.assertEqual(data[3]["account_id"], 3)
        self.assertEqual(data[3]["ga_account_id"], None)
        self.assertEqual(data[3]["ga_web_property_id"], None)
        self.assertEqual(data[3]["service_email"], None)
        self.assertEqual(data[4]["account_id"], 1000)
        self.assertEqual(data[4]["ga_account_id"], None)
        self.assertEqual(data[4]["ga_web_property_id"], None)
        self.assertEqual(data[4]["service_email"], None)

    def test_get_ga_accounts_since_yesterday_with_additional_campaigns(self):
        self.campaign.settings.update(None, ga_property_id="UA-123-4")

        response = self.client.get(
            reverse("k1api.ga_accounts"), QUERY_STRING=urllib.parse.urlencode({"campaigns": "1"})
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]["account_id"], 1)
        self.assertEqual(data[0]["ga_account_id"], "123")
        self.assertEqual(data[0]["ga_web_property_id"], "UA-123-4")
        self.assertEqual(data[0]["service_email"], None)
        self.assertEqual(data[1]["account_id"], 2)
        self.assertEqual(data[1]["ga_account_id"], None)
        self.assertEqual(data[1]["ga_web_property_id"], None)
        self.assertEqual(data[1]["service_email"], None)
        self.assertEqual(data[2]["account_id"], 3)
        self.assertEqual(data[2]["ga_account_id"], None)
        self.assertEqual(data[2]["ga_web_property_id"], None)
        self.assertEqual(data[2]["service_email"], None)
        self.assertEqual(data[3]["account_id"], 1000)
        self.assertEqual(data[3]["ga_account_id"], None)
        self.assertEqual(data[3]["ga_web_property_id"], None)
        self.assertEqual(data[3]["service_email"], None)
