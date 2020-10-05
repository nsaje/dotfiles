import sys
from random import randint

from secretcrypt import Secret

import core.features
import core.models
import dash.models
from apt.common.db_queries import get_count_estimate

from ..base.test_case import APTTestCase
from ..common import z1_client

API_URL = "https://one.zemanta.com/rest/v1/"


SECRET = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QHM5OcD7993DH6SuIW/llTJAAAA4zCB4AYJKoZIhvcNAQcGoIHSMIHPAgEAMIHJBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDLkP5aT1PChblhxkjwIBEICBm4kxsqARbMnxlgYODO4s0Dj27zAFxQlTghkikkF4sMMhd0jr4P0yKfFHd9JbgXSTNI6SSdolaI3XcCgqiHid2FOsnAzP/FuVckFUAUNqYhgZbLKYK1mPPDtlDMOxt2RZlo60LMfnlsUWQTFf7Pi6eBjC2mkB1m4VBD95dwlD/zLdufx6sBCuWtf1zn3YNR4n01SmJNhchX38j7b3"
    )
    .get()
    .decode("utf-8")
)


class APTSmokeTestCase(APTTestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = z1_client.Z1Client("eqWbmcKR7hDbf1ZjLS2ZpKR5oddOv8ZCfiybZ0f7", SECRET)
        cls.account_count = core.models.Account.objects.count()
        cls.audience_count = get_count_estimate("dash_audience")
        cls.campaign_count = get_count_estimate("dash_campaign")
        cls.ad_group_count = get_count_estimate("dash_adgroup")

    def call_and_assert_ok(self, url, params=None):
        r = self.client.make_api_call(url=API_URL + url, method="GET", params=params)
        self.assertEqual(r.status_code, 200)

    def get_random_index(self, max):
        return randint(0, max - 1)


class APISmokeTestAccountsTestCase(APTSmokeTestCase):
    def test_get_accounts_list(self):
        self.call_and_assert_ok(url="accounts/")

    def test_get_account(self):
        account_id = self.get_random_index(self.account_count)
        sys.stderr.write("account_id: " + str(account_id) + "\n")
        account = core.models.Account.objects.order_by().all()[account_id]
        self.call_and_assert_ok(url="accounts/{accountId}", params={"accountId": account.id})

    def test_get_account_credit(self):
        credit_line_item_count = get_count_estimate("dash_creditlineitem")
        cli_id = self.get_random_index(credit_line_item_count)
        sys.stderr.write("creditlineitem_id: " + str(cli_id) + "\n")
        credit_line_item = core.features.bcm.credit_line_item.CreditLineItem.objects.order_by().all()[cli_id]
        self.call_and_assert_ok(
            url="{account_id}/credits/{creditId}",
            params={"accountId": credit_line_item.account, "credit_id": credit_line_item.id},
        )

    def test_get_account_credits_list(self):
        account = core.models.Account.objects.all()[self.get_random_index(self.account_count)]
        self.call_and_assert_ok(url="accounts/{accountId}/credits/", params={"account_id": account.id})

    def test_get_pixel_detail(self):
        conversion_pixel_count = get_count_estimate("dash_conversionpixel")
        creditline_id = self.get_random_index(conversion_pixel_count)
        sys.stderr.write("conversionpixel_id: " + str(creditline_id) + "\n")
        conversion_pixel = core.models.ConversionPixel.objects.order_by().all()[creditline_id]
        self.call_and_assert_ok(
            url="accounts/{accountId}/pixels/{pixelId}",
            params={"account_id": conversion_pixel.account, "pixel_id": conversion_pixel.id},
        )

    def test_get_pixel_list(self):
        account = core.models.Account.objects.order_by().all()[self.get_random_index(self.account_count)]
        self.call_and_assert_ok(url="rest/v1/accounts/{accountId}/pixels/", params={"account_id": account.id})

    def test_get_audience_details(self):
        audience = (
            dash.models.Audience.objects.order_by()
            .all()
            .select_related("pixel")[self.get_random_index(self.audience_count)]
        )
        self.call_and_assert_ok(
            url="rest/v1/accounts/{accountId}/audiences/{audienceId}",
            params={"account_id": audience.pixel.account, "audience_id": audience.id},
        )

    def test_get_audience_list(self):
        audience = (
            dash.models.Audience.objects.order_by()
            .all()
            .select_related("pixel")[self.get_random_index(self.audience_count)]
        )
        self.call_and_assert_ok(
            url="rest/v1/accounts/{accountId}/audiences/{?includeArchived}",
            params={"account_id": audience.pixel.account},
        )


class APISmokeTestCampaignsTestCase(APTSmokeTestCase):
    def test_get_campaign_details(self):
        campaign = core.models.Campaign.objects.order_by().all()[self.get_random_index(self.campaign_count)]
        self.call_and_assert_ok("campaigns/{campaignId}", params={"campaign_id": campaign.id})

    def test_get_campaigns_list(self):
        self.call_and_assert_ok("campaigns/{?includeArchived}")

    def test_get_campaign_performance(self):
        campaign = core.models.Campaign.objects.order_by().all()[self.get_random_index(self.campaign_count)]
        self.call_and_assert_ok(
            "campaigns/{campaignId}/stats/{?from,to}",
            params={"campaign_id": campaign.id, "from": "2016-11-18", "to": "2016-11-18"},
        )

    def test_get_campaign_budgets_list(self):
        campaign = core.models.Campaign.objects.order_by().all()[self.get_random_index(self.campaign_count)]
        self.call_and_assert_ok("campaigns/{campaignId}/budgets/", params={"campaign_id": campaign.id})

    def test_get_campaign_budget(self):
        budget_count = get_count_estimate("dash_budgetlineitem")
        budget = core.features.bcm.BudgetLineItem.objects.order_by().all()[self.get_random_index(budget_count)]
        self.call_and_assert_ok(
            "campaigns/{campaignId}/budgets/{budgetId}", params={"campaign_id": budget.campaign, "budget_id": budget.id}
        )

    def test_get_campaign_goals_list(self):
        campaign = core.models.Campaign.objects.order_by().all()[self.get_random_index(self.campaign_count)]
        self.call_and_assert_ok("campaigns/{campaignId}/goals/", params={"campaign_id": campaign.id})

    def test_get_campaign_goals_details(self):
        goal_count = get_count_estimate("dash_campaigngoal")
        goal = core.features.goals.CampaignGoal.objects.order_by().all()[self.get_random_index(goal_count)]
        self.call_and_assert_ok(
            "campaigns/{campaignId}/budgets/{budgetId}", params={"campaign_id": goal.campaign, "goal_id": goal.id}
        )


class APISmokeTestAdGroupsTestCase(APTSmokeTestCase):
    def test_get_adgroup_details(self):
        ad_group = core.models.AdGroup.objects.order_by().all()[self.get_random_index(self.ad_group_count)]
        self.call_and_assert_ok("adgroups/{adGroupId}", params={"ad_group_id": ad_group.id})

    def test_get_adgroup_list(self):
        campaign = core.models.Campaign.objects.order_by().all()[self.get_random_index(self.campaign_count)]
        self.call_and_assert_ok("adgroups/{?campaignId,accountId,includeArchived}", params={"campaign_id": campaign.id})

    def test_get_adgroup_sources_settings(self):
        ad_group = core.models.AdGroup.objects.order_by().all()[self.get_random_index(self.ad_group_count)]
        self.call_and_assert_ok("adgroups/{adGroupId}/sources/", params={"ad_group_id": ad_group.id})

    def test_get_adgroup_sources_settings_RTB(self):
        ad_group = core.models.AdGroup.objects.order_by().all()[self.get_random_index(self.ad_group_count)]
        self.call_and_assert_ok("adgroups/{adGroupId}/sources/rtb/", params={"ad_group_id": ad_group.id})

    def test_get_bid_modifiers(self):
        ad_group = core.models.AdGroup.objects.order_by().all()[self.get_random_index(self.ad_group_count)]
        self.call_and_assert_ok("adgroups/{adGroupId}/bidmodifiers/{?type}", params={"ad_group_id": ad_group.id})

    def test_get_bid_modifier_for_ad_group(self):
        bid_modifier_count = get_count_estimate("dash_bidmodifier")
        bid_modifier = dash.models.BidModifier.objects.order_by().all()[self.get_random_index(bid_modifier_count)]
        self.call_and_assert_ok(
            "adgroups/{adGroupId}/bidmodifiers/{bidModifierId}",
            params={"ad_group_id": bid_modifier.ad_group, "bidModifierId": bid_modifier.id},
        )


class APTSmokeTestContentTestCase(APTSmokeTestCase):
    def test_upload_batch_status(self):
        upload_batch_count = get_count_estimate("dash_uploadbatch")
        upload_batch = dash.models.UploadBatch.objects.order_by().all()[self.get_random_index(upload_batch_count)]
        self.call_and_assert_ok("contentads/batch/{batchId}", params={"batch_id": upload_batch.id})

    def test_list_contentads(self):
        ad_group = core.models.AdGroup.objects.order_by().all()[self.get_random_index(self.ad_group_count)]
        self.call_and_assert_ok("contentads/{?adGroupId}", params={"ad_group_id": ad_group.id})

    def test_get_contentad_details(self):
        content_ad_count = get_count_estimate("dash_contentad")
        content_ad = core.models.ContentAd.objects.order_by().all()[self.get_random_index(content_ad_count)]
        self.call_and_assert_ok("contentads/{contentAdId}", params={"content_ad_id": content_ad.id})


class APTSmokeTestPublishersTestCase(APTSmokeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.publisher_group_count = get_count_estimate("dash_publishergroup")

    def test_list_publisher_groups(self):
        account = core.models.Account.objects.order_by().all()[self.get_random_index(self.account_count)]
        self.call_and_assert_ok(url="accounts/{accountId}/publishergroups/", params={"accountId": account.id})

    def test_get_publisher_groups_details(self):
        publisher_group = core.features.publisher_groups.PublisherGroup.objects.order_by().all()[
            self.get_random_index(self.publisher_group_count)
        ]
        self.call_and_assert_ok(
            url="accounts/{accountId}/publishergroups/",
            params={"accountId": publisher_group.account, "publisher_group_id": publisher_group.id},
        )

    def test_list_publisher_groups_entries(self):
        publisher_group = core.features.publisher_groups.PublisherGroup.objects.order_by().all()[
            self.get_random_index(self.publisher_group_count)
        ]
        self.call_and_assert_ok(
            url="publishergroups/{publisherGroupId}/entries/{?offset,limit}",
            params={"publisher_group_id": publisher_group.id, "limit": 100},
        )

    def test_get_publisher_group_entry(self):
        publisher_group_entry_count = dash.models.PublisherGroupEntry.objects.count()
        publisher_group_entry = dash.models.PublisherGroupEntry.objects.order_by().all()[
            self.get_random_index(publisher_group_entry_count)
        ]
        self.call_and_assert_ok(
            url="publishergroups/{publisherGroupId}/entries/{entryId}",
            params={"publisher_group_id": publisher_group_entry.publisher_group, "entry_id": publisher_group_entry.id},
        )

    def test_get_publisher_status(self):
        ad_group = core.models.AdGroup.objects.order_by().all()[self.get_random_index(self.ad_group_count)]
        self.call_and_assert_ok("adgroups/{adGroupId}/publishers/", params={"ad_group_id": ad_group.id})


class APTSmokeTestReportsTestCase(APTSmokeTestCase):
    def test_report_job_status(self):
        report_job_count = get_count_estimate("restapi_reportjob")
        report_job = dash.features.reports.reportjob.ReportJob.objects.order_by().all()[
            self.get_random_index(report_job_count)
        ]
        self.call_and_assert_ok("reports/{jobId}", params={"job_id": report_job.id})


class APTSmokeTestUtilsTestCase(APTSmokeTestCase):
    def test_list_geolocations(self):
        self.call_and_assert_ok("geolocations/{?keys,types,nameContains,limit,offset}")

    def test_list_bluekai_categories(self):
        self.call_and_assert_ok("bluekai/taxonomy/")

    def test_list_sources(self):
        self.call_and_assert_ok("sources/{?limit,offset}")
