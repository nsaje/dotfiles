from random import randint
from typing import Union

from django.db import models
from secretcrypt import Secret  # type: ignore

import core.features
import core.models
import dash.models

from ..base.test_case import APTTestCase
from ..common import z1_client

SECRET = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QHM5OcD7993DH6SuIW/llTJAAAA4zCB4AYJKoZIhvcNAQcGoIHSMIHPAgEAMIHJBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDLkP5aT1PChblhxkjwIBEICBm4kxsqARbMnxlgYODO4s0Dj27zAFxQlTghkikkF4sMMhd0jr4P0yKfFHd9JbgXSTNI6SSdolaI3XcCgqiHid2FOsnAzP/FuVckFUAUNqYhgZbLKYK1mPPDtlDMOxt2RZlo60LMfnlsUWQTFf7Pi6eBjC2mkB1m4VBD95dwlD/zLdufx6sBCuWtf1zn3YNR4n01SmJNhchX38j7b3"
    )
    .get()
    .decode("utf-8")
)

API_URL = "https://one.zemanta.com/rest/v1/"
RETRY_LIMIT = 10
DB_MODEL = Union[
    core.models.account.model.Account,
    core.features.bcm.credit_line_item.CreditLineItem,
    core.features.audiences.audience.model.Audience,
    core.models.conversion_pixel.model.ConversionPixel,
    core.models.Campaign,
    core.features.bcm.budget_line_item.BudgetLineItem,
    core.features.goals.campaign_goal.model.CampaignGoal,
    core.models.AdGroup,
    dash.models.BidModifier,
    dash.models.UploadBatch,
    core.models.ContentAd,
    core.features.publisher_groups.PublisherGroup,
    dash.models.PublisherGroupEntry,
    dash.features.reports.reportjob.ReportJob,
]


class APTSmokeTestCase(APTTestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = z1_client.Z1Client("eqWbmcKR7hDbf1ZjLS2ZpKR5oddOv8ZCfiybZ0f7", SECRET)

    def call_and_assert_ok(self, url: str, params: dict = None) -> None:
        r = self.client.make_api_call(url=API_URL + url, method="GET", params=params)  # type: ignore
        self.assertEqual(r.status_code, 200)

    def get_random_index(self, max: int) -> int:
        return randint(0, max - 1)

    def get_id_with_retries(self, queryset: models.QuerySet, count: int) -> DB_MODEL:
        for attempt in range(RETRY_LIMIT):
            try:
                print(type(queryset[self.get_random_index(count)]))
                print(f"succeed: {attempt}")
                return queryset[self.get_random_index(count)]
            except IndexError as error:
                print(f"attempt failure: {attempt}")
                exc = error
        raise exc


class APISmokeTestAccountsTestCase(APTSmokeTestCase):
    def test_get_accounts_list(self):
        self.call_and_assert_ok(url="accounts/")

    def test_get_account(self):
        account = core.models.Account.objects.last()
        self.call_and_assert_ok(url="accounts/{accountId}", params={"accountId": account.id})

    def test_get_account_credit(self):
        credit_line_item = core.features.bcm.credit_line_item.CreditLineItem.objects.last()
        self.call_and_assert_ok(
            url="{account_id}/credits/{creditId}",
            params={"accountId": credit_line_item.account, "credit_id": credit_line_item.id},
        )

    def test_get_account_credits_list(self):
        account = core.models.Account.objects.last()
        self.call_and_assert_ok(url="accounts/{accountId}/credits/", params={"account_id": account.id})

    def test_get_pixel_detail(self):
        conversion_pixel = core.models.ConversionPixel.objects.last()
        self.call_and_assert_ok(
            url="accounts/{accountId}/pixels/{pixelId}",
            params={"account_id": conversion_pixel.account, "pixel_id": conversion_pixel.id},
        )

    def test_get_pixel_list(self):
        account = core.models.Account.objects.last()
        self.call_and_assert_ok(url="rest/v1/accounts/{accountId}/pixels/", params={"account_id": account.id})

    def test_get_audience_details(self):
        audience = dash.models.Audience.objects.select_related("pixel").last()
        self.call_and_assert_ok(
            url="rest/v1/accounts/{accountId}/audiences/{audienceId}",
            params={"account_id": audience.pixel.account, "audience_id": audience.id},
        )

    def test_get_audience_list(self):
        audience = dash.models.Audience.objects.select_related("pixel").last()
        self.call_and_assert_ok(
            url="rest/v1/accounts/{accountId}/audiences/{?includeArchived}",
            params={"account_id": audience.pixel.account},
        )


class APISmokeTestCampaignsTestCase(APTSmokeTestCase):
    def test_get_campaign_details(self):
        campaign = core.models.Campaign.objects.last()
        self.call_and_assert_ok("campaigns/{campaignId}", params={"campaign_id": campaign.id})

    def test_get_campaigns_list(self):
        self.call_and_assert_ok("campaigns/{?includeArchived}")

    def test_get_campaign_performance(self):
        campaign = core.models.Campaign.objects.last()
        self.call_and_assert_ok(
            "campaigns/{campaignId}/stats/{?from,to}",
            params={"campaign_id": campaign.id, "from": "2016-11-18", "to": "2016-11-18"},
        )

    def test_get_campaign_budgets_list(self):
        campaign = core.models.Campaign.objects.last()
        self.call_and_assert_ok("campaigns/{campaignId}/budgets/", params={"campaign_id": campaign.id})

    def test_get_campaign_budget(self):
        budget = core.features.bcm.BudgetLineItem.objects.last()
        self.call_and_assert_ok(
            "campaigns/{campaignId}/budgets/{budgetId}", params={"campaign_id": budget.campaign, "budget_id": budget.id}
        )

    def test_get_campaign_goals_list(self):
        campaign = core.models.Campaign.objects.last()
        self.call_and_assert_ok("campaigns/{campaignId}/goals/", params={"campaign_id": campaign.id})

    def test_get_campaign_goals_details(self):
        goal = core.features.goals.CampaignGoal.objects.last()
        self.call_and_assert_ok(
            "campaigns/{campaignId}/budgets/{budgetId}", params={"campaign_id": goal.campaign, "goal_id": goal.id}
        )


class APISmokeTestAdGroupsTestCase(APTSmokeTestCase):
    def test_get_adgroup_details(self):
        ad_group = core.models.AdGroup.objects.last()
        self.call_and_assert_ok("adgroups/{adGroupId}", params={"ad_group_id": ad_group.id})

    def test_get_adgroup_list(self):
        campaign = core.models.Campaign.objects.last()
        self.call_and_assert_ok("adgroups/{?campaignId,accountId,includeArchived}", params={"campaign_id": campaign.id})

    def test_get_adgroup_sources_settings(self):
        ad_group = core.models.AdGroup.objects.last()
        self.call_and_assert_ok("adgroups/{adGroupId}/sources/", params={"ad_group_id": ad_group.id})

    def test_get_adgroup_sources_settings_RTB(self):
        ad_group = core.models.AdGroup.objects.last()
        self.call_and_assert_ok("adgroups/{adGroupId}/sources/rtb/", params={"ad_group_id": ad_group.id})

    def test_get_bid_modifiers(self):
        ad_group = core.models.AdGroup.objects.last()
        self.call_and_assert_ok("adgroups/{adGroupId}/bidmodifiers/{?type}", params={"ad_group_id": ad_group.id})

    def test_get_bid_modifier_for_ad_group(self):
        bid_modifier = dash.models.BidModifier.objects.last()
        self.call_and_assert_ok(
            "adgroups/{adGroupId}/bidmodifiers/{bidModifierId}",
            params={"ad_group_id": bid_modifier.ad_group, "bidModifierId": bid_modifier.id},
        )


class APTSmokeTestContentTestCase(APTSmokeTestCase):
    def test_upload_batch_status(self):
        upload_batch = dash.models.UploadBatch.objects.last()
        self.call_and_assert_ok("contentads/batch/{batchId}", params={"batch_id": upload_batch.id})

    def test_list_contentads(self):
        ad_group = core.models.AdGroup.objects.last()
        self.call_and_assert_ok("contentads/{?adGroupId}", params={"ad_group_id": ad_group.id})

    def test_get_contentad_details(self):
        content_ad = core.models.ContentAd.objects.last()
        self.call_and_assert_ok("contentads/{contentAdId}", params={"content_ad_id": content_ad.id})


class APTSmokeTestPublishersTestCase(APTSmokeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.publisher_group = core.features.publisher_groups.PublisherGroup.objects.last()

    def test_list_publisher_groups(self):
        account = core.models.Account.objects.last()
        self.call_and_assert_ok(url="accounts/{accountId}/publishergroups/", params={"accountId": account.id})

    def test_get_publisher_groups_details(self):
        self.call_and_assert_ok(
            url="accounts/{accountId}/publishergroups/",
            params={"accountId": self.publisher_group.account, "publisher_group_id": self.publisher_group.id},
        )

    def test_list_publisher_groups_entries(self):
        self.call_and_assert_ok(
            url="publishergroups/{publisherGroupId}/entries/{?offset,limit}",
            params={"publisher_group_id": self.publisher_group.id, "limit": 100},
        )

    def test_get_publisher_group_entry(self):
        publisher_group_entry = dash.models.PublisherGroupEntry.objects.last()
        self.call_and_assert_ok(
            url="publishergroups/{publisherGroupId}/entries/{entryId}",
            params={"publisher_group_id": publisher_group_entry.publisher_group, "entry_id": publisher_group_entry.id},
        )

    def test_get_publisher_status(self):
        ad_group = core.models.AdGroup.objects.last()
        self.call_and_assert_ok("adgroups/{adGroupId}/publishers/", params={"ad_group_id": ad_group.id})


class APTSmokeTestReportsTestCase(APTSmokeTestCase):
    def test_report_job_status(self):
        report_job = dash.features.reports.reportjob.ReportJob.objects.last()
        self.call_and_assert_ok("reports/{jobId}", params={"job_id": report_job.id})


class APTSmokeTestUtilsTestCase(APTSmokeTestCase):
    def test_list_geolocations(self):
        self.call_and_assert_ok("geolocations/{?keys,types,nameContains,limit,offset}")

    def test_list_bluekai_categories(self):
        self.call_and_assert_ok("bluekai/taxonomy/")

    def test_list_sources(self):
        self.call_and_assert_ok("sources/{?limit,offset}")
