import datetime
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.urls import reverse

import dash.constants
import dash.features.ga
import dash.features.geolocation
import dash.models

from .base_test import K1APIBaseTest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GAAccountsTest(K1APIBaseTest):
    def test_get_ga_accounts(self):
        dash.features.ga.GALinkedAccounts.objects.create(
            customer_ga_account_id="123", zem_ga_account_email="a1@gapps.com", has_read_and_analyze=True
        )

        response = self.client.get(reverse("k1api.ga_accounts"))

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data["ga_accounts"]), 2)
        self.assertEqual(data["ga_accounts"][0]["account_id"], 1)
        self.assertEqual(data["ga_accounts"][0]["ga_account_id"], "123")
        self.assertEqual(data["ga_accounts"][0]["ga_web_property_id"], "UA-123-2")
        self.assertEqual(data["ga_accounts"][1]["account_id"], 2)
        self.assertEqual(data["ga_accounts"][1]["ga_account_id"], "123")
        self.assertEqual(data["ga_accounts"][1]["ga_web_property_id"], "UA-123-3")

        self.assertEqual(data["service_email_mapping"], {"123": "a1@gapps.com"})

    def test_get_ga_accounts_since_ever(self):
        campaign_settings = dash.models.Campaign.objects.get(pk=1).get_current_settings().copy_settings()
        campaign_settings.ga_property_id = "UA-123-4"
        campaign_settings.save(None)

        response = self.client.get(
            reverse("k1api.ga_accounts"), QUERY_STRING=urllib.parse.urlencode({"date_since": "2014-07-01"})
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data["ga_accounts"]), 5)
        self.assertEqual(
            list(data["ga_accounts"]),
            [
                {"ga_web_property_id": "UA-123-2", "account_id": 1, "ga_account_id": "123"},
                {"ga_web_property_id": "UA-123-4", "account_id": 1, "ga_account_id": "123"},
                {"ga_web_property_id": "UA-123-0", "account_id": 2, "ga_account_id": "123"},
                {"ga_web_property_id": "UA-123-1", "account_id": 2, "ga_account_id": "123"},
                {"ga_web_property_id": "UA-123-3", "account_id": 2, "ga_account_id": "123"},
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

        self.assertEqual(len(data["ga_accounts"]), 3)
        self.assertEqual(data["ga_accounts"][0]["account_id"], 1)
        self.assertEqual(data["ga_accounts"][0]["ga_account_id"], "123")
        self.assertEqual(data["ga_accounts"][0]["ga_web_property_id"], "UA-123-2")
        self.assertEqual(data["ga_accounts"][1]["account_id"], 1)
        self.assertEqual(data["ga_accounts"][1]["ga_account_id"], "123")
        self.assertEqual(data["ga_accounts"][1]["ga_web_property_id"], "UA-123-4")
        self.assertEqual(data["ga_accounts"][2]["account_id"], 2)
        self.assertEqual(data["ga_accounts"][2]["ga_account_id"], "123")
        self.assertEqual(data["ga_accounts"][2]["ga_web_property_id"], "UA-123-3")

    def test_get_ga_accounts_since_yesterday_with_additional_campaigns(self):
        self.campaign.settings.update(None, ga_property_id="UA-123-4")

        response = self.client.get(
            reverse("k1api.ga_accounts"), QUERY_STRING=urllib.parse.urlencode({"campaigns": "1"})
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data["ga_accounts"]), 1)
        self.assertEqual(data["ga_accounts"][0]["account_id"], 1)
        self.assertEqual(data["ga_accounts"][0]["ga_account_id"], "123")
        self.assertEqual(data["ga_accounts"][0]["ga_web_property_id"], "UA-123-4")
