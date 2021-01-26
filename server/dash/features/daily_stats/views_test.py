import copy
import datetime
import json
from decimal import Decimal

from django.test import Client
from django.urls import reverse
from mock import patch

from dash import constants
from dash import models
from utils.base_test_case import BaseTestCase
from utils.test_helper import fake_request
from zemauth.models import User


class BaseDailyStatsTestCase(BaseTestCase):
    fixtures = ["test_api.yaml", "test_views.yaml"]

    def setUp(self):
        password = "secret"
        self.user = User.objects.get(pk=2)

        self.client.login(username=self.user.email, password=password)

        self.patcher = patch("stats.api_dailystats.query", autospec=True)
        self.mock_query = self.patcher.start()

        self.date = datetime.date(2015, 2, 22)

    def tearDown(self):
        self.patcher.stop()

    def _prepare_mock(self, group_key, group_id):
        mock_stats1 = [{"day": self.date.isoformat(), "etfm_cpc": "0.0100", "local_etfm_cpc": "0.0200", "clicks": 1000}]
        mock_stats2 = [
            {
                "day": self.date.isoformat(),
                "etfm_cpc": "0.0200",
                "local_etfm_cpc": "0.0400",
                "clicks": 1500,
                group_key: group_id,
            }
        ]
        self.mock_query.side_effect = [mock_stats1, mock_stats2]

    def _get_params(
        self,
        selected_ids=None,
        select_all=False,
        not_selected_ids=None,
        select_batch=None,
        agencies=None,
        account_types=None,
    ):
        params = {
            "metrics": ["etfm_cpc", "clicks"],
            "totals": True,
            "start_date": self.date.isoformat(),
            "end_date": self.date.isoformat(),
        }

        if agencies:
            params["filtered_agencies"] = agencies
        if account_types:
            params["filtered_account_types"] = account_types
        if select_all:
            params["select_all"] = True
        if selected_ids:
            params["selected_ids"] = selected_ids
        if not_selected_ids:
            params["not_selected_ids"] = not_selected_ids
        if select_batch:
            params["select_batch"] = select_batch

        return params

    def _assert_response(
        self,
        response,
        selected_id,
        selected_name,
        with_conversion_goals=True,
        with_pixels=True,
        with_goal_fields=True,
        with_cpa_fields=True,
        conversion_goals=None,
        currency=constants.Currency.USD,
    ):
        json_blob = json.loads(response.content)
        expected_response = {
            "data": {
                "chart_data": [
                    {
                        "id": "totals",
                        "name": "Totals",
                        "series_data": {
                            "clicks": [[self.date.isoformat(), 1000]],
                            "etfm_cpc": [
                                [self.date.isoformat(), "0.0100" if currency == constants.Currency.USD else "0.0200"]
                            ],
                        },
                    },
                    {
                        "id": selected_id,
                        "name": selected_name,
                        "series_data": {
                            "clicks": [[self.date.isoformat(), 1500]],
                            "etfm_cpc": [
                                [self.date.isoformat(), "0.0200" if currency == constants.Currency.USD else "0.0400"]
                            ],
                        },
                    },
                ],
                "currency": currency,
            },
            "success": True,
        }

        if with_conversion_goals:
            if conversion_goals is not None:
                expected_response["data"]["conversion_goals"] = conversion_goals
            else:
                expected_response["data"]["conversion_goals"] = [
                    {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                    {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                    {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                    {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                ]

        if with_pixels:
            expected_response["data"]["pixels"] = [{"prefix": "pixel_1", "name": "test"}]

        if with_goal_fields:
            expected_response["data"]["campaign_goals"] = {}
            expected_response["data"]["goal_fields"] = {
                "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                "avg_etfm_cost_per_non_bounced_visit": {
                    "id": "Cost per Non-Bounced Visit",
                    "name": "Cost per Non-Bounced Visit",
                },
                "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                "etfm_cpc": {"id": "CPC", "name": "CPC"},
                "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                "video_etfm_cpcv": {"id": "Cost per Completed Video View", "name": "Cost per Completed Video View"},
            }

        if with_cpa_fields:
            expected_response["data"]["goal_fields"]["avg_etfm_cost_per_conversion_goal_2"] = {
                "id": "avg_etfm_cost_per_conversion_goal_2",
                "name": "$CPA - test conversion goal 2",
            }
            expected_response["data"]["goal_fields"]["avg_etfm_cost_per_conversion_goal_3"] = {
                "id": "avg_etfm_cost_per_conversion_goal_3",
                "name": "$CPA - test conversion goal 3",
            }
            expected_response["data"]["goal_fields"]["avg_etfm_cost_per_conversion_goal_4"] = {
                "id": "avg_etfm_cost_per_conversion_goal_4",
                "name": "$CPA - test conversion goal 4",
            }
            expected_response["data"]["goal_fields"]["avg_etfm_cost_per_conversion_goal_5"] = {
                "id": "avg_etfm_cost_per_conversion_goal_5",
                "name": "$CPA - test conversion goal 5",
            }
            expected_response["data"]["goal_fields"]["avg_etfm_cost_per_pixel_1_168"] = {
                "id": "avg_etfm_cost_per_pixel_1_168",
                "name": "$CPA - test conversion goal",
            }

        self.assertDictEqual(expected_response, json_blob)

        """
            'campaign_goals': {
                'reports': [],
                'conversions': ListMatcher([
                    {'id': 'Test Cg', 'name': 'test conversion goal 5'},
                    {'id': 'conversion_goal_4', 'name': 'test conversion goal 4'},
                    {'id': 'conversion_goal_3', 'name': 'test conversion goal 3'},
                    {'id': 'conversion_goal_2', 'name': 'test conversion goal 2'},
                    {'id': 'conversion_goal_1', 'name': 'test conversion goal'},
                ]),
            },

        """


class AccountsDailyStatsTestCase(BaseDailyStatsTestCase):

    # def test_invalid_metrics(self):
    #     source_id = 3

    #     self._prepare_mock('source_id', source_id)

    #     params = self._get_params(selected_ids=[source_id])
    #     params['metrics'] = ['invalidmetric']
    #     response = self.client.get(
    #         reverse('accounts_sources_daily_stats'),
    #         params,
    #         follow=True
    #     )
    #     self.assertEqual(400, response.status_code)

    def test_get_by_source(self):
        source_id = 3

        self._prepare_mock("source_id", source_id)

        response = self.client.get(
            reverse("accounts_sources_daily_stats"), self._get_params(selected_ids=[source_id]), follow=True
        )

        self.assertEqual(200, response.status_code)

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(
            response,
            source_id,
            source.name,
            with_conversion_goals=False,
            with_pixels=False,
            with_goal_fields=False,
            with_cpa_fields=False,
        )

    def test_get_by_source_join_selected(self):
        source_ids = [3, 4, 5, 6]

        self._prepare_mock(None, None)

        response = self.client.get(
            reverse("accounts_sources_daily_stats"), self._get_params(selected_ids=source_ids), follow=True
        )

        self.assertEqual(200, response.status_code)
        self._assert_response(
            response,
            "selected",
            "Selected",
            with_conversion_goals=False,
            with_pixels=False,
            with_goal_fields=False,
            with_cpa_fields=False,
        )

    def test_get_by_account(self):
        account_id = 2

        self._prepare_mock("account_id", account_id)

        response = self.client.get(
            reverse("accounts_accounts_daily_stats"), self._get_params(selected_ids=[account_id]), follow=True
        )

        self.assertEqual(200, response.status_code)

        account = models.Account.objects.get(pk=account_id)
        self._assert_response(
            response,
            account_id,
            account.name,
            with_conversion_goals=False,
            with_pixels=False,
            with_goal_fields=False,
            with_cpa_fields=False,
        )

    def test_get_by_agency(self):
        agency = models.Agency(name="test")
        agency.save(fake_request(self.user))

        response = self.client.get(
            reverse("accounts_accounts_daily_stats"),
            self._get_params(selected_ids=[], agencies=[agency.id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        acc1 = models.Account.objects.get(pk=1)
        acc1.agency = agency
        acc1.save(fake_request(self.user))

        response = self.client.get(
            reverse("accounts_accounts_daily_stats"),
            self._get_params(selected_ids=[], agencies=[agency.id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

    def test_get_by_account_type(self):
        response = self.client.get(
            reverse("accounts_accounts_daily_stats"),
            self._get_params(selected_ids=[], account_types=[constants.AccountType.TEST]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        acc1 = models.Account.objects.get(pk=1)
        acs = acc1.get_current_settings().copy_settings()
        acs.account_type = constants.AccountType.TEST
        acs.save(fake_request(self.user))

        response = self.client.get(
            reverse("accounts_accounts_daily_stats"),
            self._get_params(selected_ids=[], account_types=[constants.AccountType.TEST]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

    def test_get_by_delivery(self):
        device_id = constants.DeviceType.DESKTOP
        self._prepare_mock("device_type", device_id)

        response = self.client.get(
            reverse("accounts_delivery_daily_stats", kwargs={"delivery_dimension": "device_type"}),
            self._get_params(selected_ids=[device_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self._assert_response(
            response,
            device_id,
            constants.DeviceType.get_name(device_id),
            with_conversion_goals=False,
            with_pixels=False,
            with_goal_fields=False,
            with_cpa_fields=False,
        )

    def test_get_by_delivery_join_selected(self):
        device_ids = [
            constants.DeviceType.DESKTOP,
            constants.DeviceType.MOBILE,
            constants.DeviceType.TABLET,
            constants.DeviceType.TV,
        ]
        self._prepare_mock(None, None)

        response = self.client.get(
            reverse("accounts_delivery_daily_stats", kwargs={"delivery_dimension": "device_type"}),
            self._get_params(selected_ids=device_ids),
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self._assert_response(
            response,
            "selected",
            "Selected",
            with_conversion_goals=False,
            with_pixels=False,
            with_goal_fields=False,
            with_cpa_fields=False,
        )


class AccountDailyStatsTestCase(BaseDailyStatsTestCase):
    def test_get_by_source(self):
        source_id = 3

        self._prepare_mock("source_id", source_id)

        response = self.client.get(
            reverse("account_sources_daily_stats", kwargs={"account_id": 1}),
            self._get_params(selected_ids=[source_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(
            response, source_id, source.name, with_conversion_goals=False, with_goal_fields=False, with_cpa_fields=False
        )

    def test_get_by_source_local_currency(self):
        source_id = 3

        self._prepare_mock("source_id", source_id)

        response = self.client.get(
            reverse("account_sources_daily_stats", kwargs={"account_id": 2}),
            self._get_params(selected_ids=[source_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(
            response,
            source_id,
            source.name,
            with_conversion_goals=False,
            with_pixels=False,
            currency=constants.Currency.EUR,
            with_goal_fields=False,
            with_cpa_fields=False,
        )

    def test_get_by_campaign(self):
        campaign_id = 1

        self._prepare_mock("campaign_id", campaign_id)

        response = self.client.get(
            reverse("account_campaigns_daily_stats", kwargs={"account_id": 1}),
            self._get_params(selected_ids=[campaign_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        campaign = models.Campaign.objects.get(pk=campaign_id)
        self._assert_response(
            response,
            campaign_id,
            campaign.name,
            with_conversion_goals=False,
            with_goal_fields=False,
            with_cpa_fields=False,
        )

    def test_get_by_campaign_local_currency(self):
        campaign_id = 87

        self._prepare_mock("campaign_id", campaign_id)

        response = self.client.get(
            reverse("account_campaigns_daily_stats", kwargs={"account_id": 2}),
            self._get_params(selected_ids=[campaign_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        campaign = models.Campaign.objects.get(pk=campaign_id)
        self._assert_response(
            response,
            campaign_id,
            campaign.name,
            with_conversion_goals=False,
            with_pixels=False,
            currency=constants.Currency.EUR,
            with_goal_fields=False,
            with_cpa_fields=False,
        )

    def test_get_by_delivery(self):
        device_id = constants.DeviceType.DESKTOP
        self._prepare_mock("device_type", device_id)

        response = self.client.get(
            reverse("account_delivery_daily_stats", kwargs={"account_id": 1, "delivery_dimension": "device_type"}),
            self._get_params(selected_ids=[device_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self._assert_response(
            response,
            device_id,
            constants.DeviceType.get_name(device_id),
            with_conversion_goals=False,
            with_goal_fields=False,
            with_cpa_fields=False,
        )

    def test_get_by_delivery_local_currency(self):
        device_id = constants.DeviceType.DESKTOP
        self._prepare_mock("device_type", device_id)

        response = self.client.get(
            reverse("account_delivery_daily_stats", kwargs={"account_id": 2, "delivery_dimension": "device_type"}),
            self._get_params(selected_ids=[device_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self._assert_response(
            response,
            device_id,
            constants.DeviceType.get_name(device_id),
            with_conversion_goals=False,
            with_pixels=False,
            currency=constants.Currency.EUR,
            with_goal_fields=False,
            with_cpa_fields=False,
        )


class CampaignDailyStatsTestCase(BaseDailyStatsTestCase):
    def test_get_by_source(self):
        source_id = 3

        self._prepare_mock("source_id", source_id)

        response = self.client.get(
            reverse("campaign_sources_daily_stats", kwargs={"campaign_id": 1}),
            self._get_params(selected_ids=[source_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(response, source_id, source.name)

    def test_get_by_source_local_currency(self):
        source_id = 3

        self._prepare_mock("source_id", source_id)

        response = self.client.get(
            reverse("campaign_sources_daily_stats", kwargs={"campaign_id": 87}),
            self._get_params(selected_ids=[source_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(
            response,
            source_id,
            source.name,
            with_pixels=False,
            conversion_goals=[],
            with_goal_fields=True,
            with_cpa_fields=False,
            currency=constants.Currency.EUR,
        )

    def test_get_by_ad_group(self):
        ad_group_id = 1

        self._prepare_mock("ad_group_id", ad_group_id)

        response = self.client.get(
            reverse("campaign_ad_groups_daily_stats", kwargs={"campaign_id": 1}),
            self._get_params(selected_ids=[ad_group_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        self._assert_response(response, ad_group_id, ad_group.name)

    def test_get_by_ad_group_local_currency(self):
        ad_group_id = 876

        self._prepare_mock("ad_group_id", ad_group_id)

        response = self.client.get(
            reverse("campaign_ad_groups_daily_stats", kwargs={"campaign_id": 87}),
            self._get_params(selected_ids=[ad_group_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        self._assert_response(
            response,
            ad_group_id,
            ad_group.name,
            with_pixels=False,
            conversion_goals=[],
            with_goal_fields=True,
            with_cpa_fields=False,
            currency=constants.Currency.EUR,
        )

    def test_get_campaign_goals(self):
        ad_group_id = 1

        self._prepare_mock("ad_group_id", ad_group_id)
        response = self.client.get(
            reverse("campaign_ad_groups_daily_stats", kwargs={"campaign_id": 1}),
            self._get_params(selected_ids=[ad_group_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        response_blob = json.loads(response.content)
        self.assertTrue("goal_fields" in response_blob["data"])
        self.assertTrue("campaign_goals" in response_blob["data"])

    def test_get_by_delivery(self):
        device_id = constants.DeviceType.DESKTOP
        self._prepare_mock("device_type", device_id)

        response = self.client.get(
            reverse("campaign_delivery_daily_stats", kwargs={"campaign_id": 1, "delivery_dimension": "device_type"}),
            self._get_params(selected_ids=[device_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self._assert_response(response, device_id, constants.DeviceType.get_name(device_id))

    def test_get_by_delivery_local_currency(self):
        device_id = constants.DeviceType.DESKTOP
        self._prepare_mock("device_type", device_id)

        response = self.client.get(
            reverse("campaign_delivery_daily_stats", kwargs={"campaign_id": 87, "delivery_dimension": "device_type"}),
            self._get_params(selected_ids=[device_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self._assert_response(
            response,
            device_id,
            constants.DeviceType.get_name(device_id),
            with_pixels=False,
            conversion_goals=[],
            with_goal_fields=True,
            with_cpa_fields=False,
            currency=constants.Currency.EUR,
        )


class AdGroupDailyStatsTestCase(BaseDailyStatsTestCase):
    def test_get_by_source(self):
        source_id = 3

        self._prepare_mock("source_id", source_id)

        response = self.client.get(
            reverse("ad_group_sources_daily_stats", kwargs={"ad_group_id": 1}),
            self._get_params(selected_ids=[source_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(response, source_id, source.name)

    def test_get_by_source_local_currency(self):
        source_id = 3

        self._prepare_mock("source_id", source_id)

        response = self.client.get(
            reverse("ad_group_sources_daily_stats", kwargs={"ad_group_id": 876}),
            self._get_params(selected_ids=[source_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        source = models.Source.objects.get(pk=source_id)
        self._assert_response(
            response,
            source_id,
            source.name,
            with_pixels=False,
            conversion_goals=[],
            with_goal_fields=True,
            with_cpa_fields=False,
            currency=constants.Currency.EUR,
        )

    def test_get_campaign_goals(self):
        source_id = 3
        self._prepare_mock("source_id", source_id)
        response = self.client.get(
            reverse("ad_group_sources_daily_stats", kwargs={"ad_group_id": 1}),
            self._get_params(selected_ids=[source_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        response_blob = json.loads(response.content)
        self.assertTrue("goal_fields" in response_blob["data"])
        self.assertTrue("campaign_goals" in response_blob["data"])

        self._prepare_mock("source_id", source_id)
        response = self.client.get(
            reverse("ad_group_sources_daily_stats", kwargs={"ad_group_id": 1}),
            self._get_params(selected_ids=[source_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        response_blob = json.loads(response.content)
        self.assertTrue("goal_fields" in response_blob["data"])
        self.assertTrue("campaign_goals" in response_blob["data"])

    def test_get_content_ads(self):
        content_ad_id = 3

        self._prepare_mock("content_ad_id", content_ad_id)

        response = self.client.get(
            reverse("ad_group_content_ads_daily_stats", kwargs={"ad_group_id": 1}),
            self._get_params(selected_ids=[content_ad_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self._assert_response(response, content_ad_id, content_ad.title)

    def test_get_content_ads_local_currency(self):
        content_ad_id = 8765

        self._prepare_mock("content_ad_id", content_ad_id)

        response = self.client.get(
            reverse("ad_group_content_ads_daily_stats", kwargs={"ad_group_id": 876}),
            self._get_params(selected_ids=[content_ad_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self._assert_response(
            response,
            content_ad_id,
            content_ad.title,
            with_pixels=False,
            conversion_goals=[],
            with_goal_fields=True,
            with_cpa_fields=False,
            currency=constants.Currency.EUR,
        )

    def test_get_content_ads_select_all(self):
        content_ad_id = 2

        self._prepare_mock("content_ad_id", content_ad_id)

        response = self.client.get(
            reverse("ad_group_content_ads_daily_stats", kwargs={"ad_group_id": 1}),
            self._get_params(select_all=True, not_selected_ids=[1, 3]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self._assert_response(response, content_ad_id, content_ad.title)

    def test_get_content_ads_select_batch(self):
        content_ad_id = 2

        self._prepare_mock("content_ad_id", content_ad_id)

        response = self.client.get(
            reverse("ad_group_content_ads_daily_stats", kwargs={"ad_group_id": 1}),
            self._get_params(select_batch=1, not_selected_ids=[1]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self._assert_response(response, content_ad_id, content_ad.title)

    def test_get_content_ads_select_batch_selected_ids(self):
        content_ad_id = 3

        self._prepare_mock("content_ad_id", content_ad_id)

        response = self.client.get(
            reverse("ad_group_content_ads_daily_stats", kwargs={"ad_group_id": 1}),
            self._get_params(select_batch=1, not_selected_ids=[1, 2], selected_ids=[3]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        self._assert_response(response, content_ad_id, content_ad.title)

    def test_get_with_conversion_goals(self):
        created_dt = datetime.datetime.utcnow()

        models.ConversionGoal.objects.filter(name="test conversion goal 5").delete()

        # set up a campaign and conversion goal
        campaign = models.Campaign.objects.get(pk=1)

        cg1 = models.CampaignGoal.objects.create_unsafe(
            campaign=campaign, type=constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS, created_dt=created_dt
        )

        models.CampaignGoalValue.objects.create(campaign_goal=cg1, value=Decimal("10"), created_dt=created_dt)

        convg = models.ConversionGoal.objects.create_unsafe(
            campaign=campaign, type=constants.ConversionGoalType.GA, name="Test Cg", conversion_window=30, goal_id="6"
        )

        convg1 = models.CampaignGoal.objects.create_unsafe(
            campaign=campaign, conversion_goal=convg, type=constants.CampaignGoalKPI.CPA, created_dt=created_dt
        )
        models.CampaignGoalValue.objects.create(campaign_goal=convg1, value=Decimal("5"), created_dt=created_dt)

        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [
            {"day": start_date.isoformat(), "etfm_cpc": "0.0100", "clicks": 1000, "conversion_goal_5": 5},
            {"day": end_date.isoformat(), "etfm_cpc": "0.0200", "clicks": 1500, "conversion_goal_5": 6},
        ]
        self.mock_query.return_value = mock_stats

        params = {
            "totals": True,
            "metrics": ["etfm_cpc", "clicks", "conversion_goal_5"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        response = self.client.get(
            reverse("ad_group_content_ads_daily_stats", kwargs={"ad_group_id": 1}), params, follow=True
        )

        self.assertEqual(200, response.status_code)

        self.assertDictEqual(
            json.loads(response.content),
            {
                "data": {
                    "goal_fields": {
                        "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                        "avg_etfm_cost_per_pixel_1_168": {
                            "id": "avg_etfm_cost_per_pixel_1_168",
                            "name": "$CPA - test conversion goal",
                        },
                        "avg_etfm_cost_per_conversion_goal_2": {
                            "id": "avg_etfm_cost_per_conversion_goal_2",
                            "name": "$CPA - test conversion goal 2",
                        },
                        "avg_etfm_cost_per_conversion_goal_3": {
                            "id": "avg_etfm_cost_per_conversion_goal_3",
                            "name": "$CPA - test conversion goal 3",
                        },
                        "avg_etfm_cost_per_conversion_goal_4": {
                            "id": "avg_etfm_cost_per_conversion_goal_4",
                            "name": "$CPA - test conversion goal 4",
                        },
                        "avg_etfm_cost_per_conversion_goal_5": {
                            "id": "avg_etfm_cost_per_conversion_goal_5",
                            "name": "$CPA - Test Cg",
                        },
                        "etfm_cpc": {"id": "CPC", "name": "CPC"},
                        "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                        "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                        "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                        "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                        "avg_etfm_cost_per_non_bounced_visit": {
                            "id": "Cost per Non-Bounced Visit",
                            "name": "Cost per Non-Bounced Visit",
                        },
                        "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                        "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                        "video_etfm_cpcv": {
                            "id": "Cost per Completed Video View",
                            "name": "Cost per Completed Video View",
                        },
                    },
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0100"], [end_date.isoformat(), "0.0200"]],
                                "conversion_goal_5": [[start_date.isoformat(), 5], [end_date.isoformat(), 6]],
                            },
                        }
                    ],
                    "currency": constants.Currency.USD,
                    "conversion_goals": [
                        {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                        {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                        {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                        {"id": "conversion_goal_5", "name": "Test Cg"},
                    ],
                    "campaign_goals": {},
                    "pixels": [{"prefix": "pixel_1", "name": "test"}],
                },
                "success": True,
            },
        )

    def test_get_by_delivery(self):
        device_id = constants.DeviceType.DESKTOP
        self._prepare_mock("device_type", device_id)

        response = self.client.get(
            reverse("ad_group_delivery_daily_stats", kwargs={"ad_group_id": 1, "delivery_dimension": "device_type"}),
            self._get_params(selected_ids=[device_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self._assert_response(response, device_id, constants.DeviceType.get_name(device_id))

    def test_get_by_delivery_local_currency(self):
        device_id = constants.DeviceType.DESKTOP
        self._prepare_mock("device_type", device_id)

        response = self.client.get(
            reverse("ad_group_delivery_daily_stats", kwargs={"ad_group_id": 876, "delivery_dimension": "device_type"}),
            self._get_params(selected_ids=[device_id]),
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        self._assert_response(
            response,
            device_id,
            constants.DeviceType.get_name(device_id),
            with_pixels=False,
            conversion_goals=[],
            with_goal_fields=True,
            with_cpa_fields=False,
            currency=constants.Currency.EUR,
        )


@patch("stats.api_dailystats.query")
class AdGroupPublishersDailyStatsTestCase(BaseTestCase):
    fixtures = ["test_views"]

    def setUp(self):
        password = "secret"
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [
            {"day": start_date.isoformat(), "etfm_cpc": "0.0100", "local_etfm_cpc": "0.0200", "clicks": 1000},
            {"day": end_date.isoformat(), "etfm_cpc": "0.0200", "local_etfm_cpc": "0.0400", "clicks": 1500},
        ]

        mock_query.return_value = copy.deepcopy(mock_stats)

        params = {
            "metrics": ["etfm_cpc", "clicks"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "totals": "true",
        }

        response = self.client.get(
            reverse("ad_group_publishers_daily_stats", kwargs={"ad_group_id": 987}), params, follow=True
        )
        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "goal_fields": {
                        "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                        "avg_etfm_cost_per_pixel_1_168": {
                            "id": "avg_etfm_cost_per_pixel_1_168",
                            "name": "$CPA - test conversion goal",
                        },
                        "avg_etfm_cost_per_conversion_goal_2": {
                            "id": "avg_etfm_cost_per_conversion_goal_2",
                            "name": "$CPA - test conversion goal 2",
                        },
                        "avg_etfm_cost_per_conversion_goal_3": {
                            "id": "avg_etfm_cost_per_conversion_goal_3",
                            "name": "$CPA - test conversion goal 3",
                        },
                        "avg_etfm_cost_per_conversion_goal_4": {
                            "id": "avg_etfm_cost_per_conversion_goal_4",
                            "name": "$CPA - test conversion goal 4",
                        },
                        "avg_etfm_cost_per_conversion_goal_5": {
                            "id": "avg_etfm_cost_per_conversion_goal_5",
                            "name": "$CPA - test conversion goal 5",
                        },
                        "etfm_cpc": {"id": "CPC", "name": "CPC"},
                        "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                        "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                        "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                        "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                        "avg_etfm_cost_per_non_bounced_visit": {
                            "id": "Cost per Non-Bounced Visit",
                            "name": "Cost per Non-Bounced Visit",
                        },
                        "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                        "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                        "video_etfm_cpcv": {
                            "id": "Cost per Completed Video View",
                            "name": "Cost per Completed Video View",
                        },
                    },
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0100"], [end_date.isoformat(), "0.0200"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.USD,
                    "conversion_goals": [
                        {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                        {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                        {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                        {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                    ],
                    "campaign_goals": {},
                    "pixels": [{"prefix": "pixel_1", "name": "test"}],
                },
                "success": True,
            },
        )

        mock_query.return_value = copy.deepcopy(mock_stats)

        response = self.client.get(
            reverse("ad_group_publishers_daily_stats", kwargs={"ad_group_id": 876}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "goal_fields": {
                        "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                        "etfm_cpc": {"id": "CPC", "name": "CPC"},
                        "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                        "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                        "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                        "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                        "avg_etfm_cost_per_non_bounced_visit": {
                            "id": "Cost per Non-Bounced Visit",
                            "name": "Cost per Non-Bounced Visit",
                        },
                        "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                        "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                        "video_etfm_cpcv": {
                            "id": "Cost per Completed Video View",
                            "name": "Cost per Completed Video View",
                        },
                    },
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0200"], [end_date.isoformat(), "0.0400"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.EUR,
                    "conversion_goals": [],
                    "campaign_goals": {},
                },
                "success": True,
            },
        )


@patch("stats.api_dailystats.query")
class AdGroupPlacementsDailyStatsTestCase(BaseTestCase):
    fixtures = ["test_views"]

    def setUp(self):
        password = "secret"
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [
            {"day": start_date.isoformat(), "etfm_cpc": "0.0100", "local_etfm_cpc": "0.0200", "clicks": 1000},
            {"day": end_date.isoformat(), "etfm_cpc": "0.0200", "local_etfm_cpc": "0.0400", "clicks": 1500},
        ]

        mock_query.return_value = copy.deepcopy(mock_stats)

        params = {
            "metrics": ["etfm_cpc", "clicks"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "totals": "true",
        }

        response = self.client.get(
            reverse("ad_group_placements_daily_stats", kwargs={"ad_group_id": 987}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "goal_fields": {
                        "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                        "avg_etfm_cost_per_pixel_1_168": {
                            "id": "avg_etfm_cost_per_pixel_1_168",
                            "name": "$CPA - test conversion goal",
                        },
                        "avg_etfm_cost_per_conversion_goal_2": {
                            "id": "avg_etfm_cost_per_conversion_goal_2",
                            "name": "$CPA - test conversion goal 2",
                        },
                        "avg_etfm_cost_per_conversion_goal_3": {
                            "id": "avg_etfm_cost_per_conversion_goal_3",
                            "name": "$CPA - test conversion goal 3",
                        },
                        "avg_etfm_cost_per_conversion_goal_4": {
                            "id": "avg_etfm_cost_per_conversion_goal_4",
                            "name": "$CPA - test conversion goal 4",
                        },
                        "avg_etfm_cost_per_conversion_goal_5": {
                            "id": "avg_etfm_cost_per_conversion_goal_5",
                            "name": "$CPA - test conversion goal 5",
                        },
                        "etfm_cpc": {"id": "CPC", "name": "CPC"},
                        "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                        "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                        "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                        "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                        "avg_etfm_cost_per_non_bounced_visit": {
                            "id": "Cost per Non-Bounced Visit",
                            "name": "Cost per Non-Bounced Visit",
                        },
                        "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                        "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                        "video_etfm_cpcv": {
                            "id": "Cost per Completed Video View",
                            "name": "Cost per Completed Video View",
                        },
                    },
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0100"], [end_date.isoformat(), "0.0200"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.USD,
                    "conversion_goals": [
                        {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                        {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                        {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                        {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                    ],
                    "campaign_goals": {},
                    "pixels": [{"prefix": "pixel_1", "name": "test"}],
                },
                "success": True,
            },
        )

        mock_query.return_value = copy.deepcopy(mock_stats)

        response = self.client.get(
            reverse("ad_group_placements_daily_stats", kwargs={"ad_group_id": 876}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "goal_fields": {
                        "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                        "etfm_cpc": {"id": "CPC", "name": "CPC"},
                        "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                        "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                        "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                        "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                        "avg_etfm_cost_per_non_bounced_visit": {
                            "id": "Cost per Non-Bounced Visit",
                            "name": "Cost per Non-Bounced Visit",
                        },
                        "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                        "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                        "video_etfm_cpcv": {
                            "id": "Cost per Completed Video View",
                            "name": "Cost per Completed Video View",
                        },
                    },
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0200"], [end_date.isoformat(), "0.0400"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.EUR,
                    "conversion_goals": [],
                    "campaign_goals": {},
                },
                "success": True,
            },
        )


@patch("stats.api_dailystats.query")
class CampaignPublishersDailyStatsTestCase(BaseTestCase):
    fixtures = ["test_views"]

    def setUp(self):
        password = "secret"
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [
            {"day": start_date.isoformat(), "etfm_cpc": "0.0100", "local_etfm_cpc": "0.0200", "clicks": 1000},
            {"day": end_date.isoformat(), "etfm_cpc": "0.0200", "local_etfm_cpc": "0.0400", "clicks": 1500},
        ]

        mock_query.return_value = copy.deepcopy(mock_stats)

        params = {
            "metrics": ["etfm_cpc", "clicks"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "totals": "true",
        }

        response = self.client.get(
            reverse("campaign_publishers_daily_stats", kwargs={"campaign_id": 1}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "goal_fields": {
                        "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                        "avg_etfm_cost_per_pixel_1_168": {
                            "id": "avg_etfm_cost_per_pixel_1_168",
                            "name": "$CPA - test conversion goal",
                        },
                        "avg_etfm_cost_per_conversion_goal_2": {
                            "id": "avg_etfm_cost_per_conversion_goal_2",
                            "name": "$CPA - test conversion goal 2",
                        },
                        "avg_etfm_cost_per_conversion_goal_3": {
                            "id": "avg_etfm_cost_per_conversion_goal_3",
                            "name": "$CPA - test conversion goal 3",
                        },
                        "avg_etfm_cost_per_conversion_goal_4": {
                            "id": "avg_etfm_cost_per_conversion_goal_4",
                            "name": "$CPA - test conversion goal 4",
                        },
                        "avg_etfm_cost_per_conversion_goal_5": {
                            "id": "avg_etfm_cost_per_conversion_goal_5",
                            "name": "$CPA - test conversion goal 5",
                        },
                        "etfm_cpc": {"id": "CPC", "name": "CPC"},
                        "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                        "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                        "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                        "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                        "avg_etfm_cost_per_non_bounced_visit": {
                            "id": "Cost per Non-Bounced Visit",
                            "name": "Cost per Non-Bounced Visit",
                        },
                        "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                        "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                        "video_etfm_cpcv": {
                            "id": "Cost per Completed Video View",
                            "name": "Cost per Completed Video View",
                        },
                    },
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0100"], [end_date.isoformat(), "0.0200"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.USD,
                    "conversion_goals": [
                        {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                        {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                        {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                        {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                    ],
                    "campaign_goals": {},
                    "pixels": [{"prefix": "pixel_1", "name": "test"}],
                },
                "success": True,
            },
        )

        mock_query.return_value = copy.deepcopy(mock_stats)

        response = self.client.get(
            reverse("campaign_publishers_daily_stats", kwargs={"campaign_id": 87}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "goal_fields": {
                        "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                        "etfm_cpc": {"id": "CPC", "name": "CPC"},
                        "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                        "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                        "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                        "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                        "avg_etfm_cost_per_non_bounced_visit": {
                            "id": "Cost per Non-Bounced Visit",
                            "name": "Cost per Non-Bounced Visit",
                        },
                        "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                        "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                        "video_etfm_cpcv": {
                            "id": "Cost per Completed Video View",
                            "name": "Cost per Completed Video View",
                        },
                    },
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0200"], [end_date.isoformat(), "0.0400"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.EUR,
                    "campaign_goals": {},
                    "conversion_goals": [],
                },
                "success": True,
            },
        )


@patch("stats.api_dailystats.query")
class CampaignPlacementDailyStatsTestCase(BaseTestCase):
    fixtures = ["test_views"]

    def setUp(self):
        password = "secret"
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [
            {"day": start_date.isoformat(), "etfm_cpc": "0.0100", "local_etfm_cpc": "0.0200", "clicks": 1000},
            {"day": end_date.isoformat(), "etfm_cpc": "0.0200", "local_etfm_cpc": "0.0400", "clicks": 1500},
        ]

        mock_query.return_value = copy.deepcopy(mock_stats)

        params = {
            "metrics": ["etfm_cpc", "clicks"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "totals": "true",
        }

        response = self.client.get(
            reverse("campaign_placements_daily_stats", kwargs={"campaign_id": 1}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "goal_fields": {
                        "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                        "avg_etfm_cost_per_pixel_1_168": {
                            "id": "avg_etfm_cost_per_pixel_1_168",
                            "name": "$CPA - test conversion goal",
                        },
                        "avg_etfm_cost_per_conversion_goal_2": {
                            "id": "avg_etfm_cost_per_conversion_goal_2",
                            "name": "$CPA - test conversion goal 2",
                        },
                        "avg_etfm_cost_per_conversion_goal_3": {
                            "id": "avg_etfm_cost_per_conversion_goal_3",
                            "name": "$CPA - test conversion goal 3",
                        },
                        "avg_etfm_cost_per_conversion_goal_4": {
                            "id": "avg_etfm_cost_per_conversion_goal_4",
                            "name": "$CPA - test conversion goal 4",
                        },
                        "avg_etfm_cost_per_conversion_goal_5": {
                            "id": "avg_etfm_cost_per_conversion_goal_5",
                            "name": "$CPA - test conversion goal 5",
                        },
                        "etfm_cpc": {"id": "CPC", "name": "CPC"},
                        "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                        "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                        "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                        "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                        "avg_etfm_cost_per_non_bounced_visit": {
                            "id": "Cost per Non-Bounced Visit",
                            "name": "Cost per Non-Bounced Visit",
                        },
                        "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                        "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                        "video_etfm_cpcv": {
                            "id": "Cost per Completed Video View",
                            "name": "Cost per Completed Video View",
                        },
                    },
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0100"], [end_date.isoformat(), "0.0200"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.USD,
                    "conversion_goals": [
                        {"id": "conversion_goal_2", "name": "test conversion goal 2"},
                        {"id": "conversion_goal_3", "name": "test conversion goal 3"},
                        {"id": "conversion_goal_4", "name": "test conversion goal 4"},
                        {"id": "conversion_goal_5", "name": "test conversion goal 5"},
                    ],
                    "campaign_goals": {},
                    "pixels": [{"prefix": "pixel_1", "name": "test"}],
                },
                "success": True,
            },
        )

        mock_query.return_value = copy.deepcopy(mock_stats)

        response = self.client.get(
            reverse("campaign_placements_daily_stats", kwargs={"campaign_id": 87}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "goal_fields": {
                        "avg_tos": {"id": "Time on Site - Seconds", "name": "Time on Site - Seconds"},
                        "etfm_cpc": {"id": "CPC", "name": "CPC"},
                        "pv_per_visit": {"id": "Pageviews per Visit", "name": "Pageviews per Visit"},
                        "bounce_rate": {"id": "Max Bounce Rate", "name": "Max Bounce Rate"},
                        "percent_new_users": {"id": "New Unique Visitors", "name": "New Unique Visitors"},
                        "avg_etfm_cost_per_visit": {"id": "Cost per Visit", "name": "Cost per Visit"},
                        "avg_etfm_cost_per_non_bounced_visit": {
                            "id": "Cost per Non-Bounced Visit",
                            "name": "Cost per Non-Bounced Visit",
                        },
                        "avg_etfm_cost_per_new_visitor": {"id": "Cost per New Visitor", "name": "Cost per New Visitor"},
                        "avg_etfm_cost_per_pageview": {"id": "Cost per Pageview", "name": "Cost per Pageview"},
                        "video_etfm_cpcv": {
                            "id": "Cost per Completed Video View",
                            "name": "Cost per Completed Video View",
                        },
                    },
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0200"], [end_date.isoformat(), "0.0400"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.EUR,
                    "campaign_goals": {},
                    "conversion_goals": [],
                },
                "success": True,
            },
        )


@patch("stats.api_dailystats.query")
class AccountPublishersDailyStatsTestCase(BaseTestCase):
    fixtures = ["test_views"]

    def setUp(self):
        password = "secret"
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [
            {"day": start_date.isoformat(), "etfm_cpc": "0.0100", "local_etfm_cpc": "0.0200", "clicks": 1000},
            {"day": end_date.isoformat(), "etfm_cpc": "0.0200", "local_etfm_cpc": "0.0400", "clicks": 1500},
        ]

        params = {
            "metrics": ["etfm_cpc", "clicks"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "totals": "true",
        }

        mock_query.return_value = copy.deepcopy(mock_stats)
        response = self.client.get(
            reverse("account_publishers_daily_stats", kwargs={"account_id": 1}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0100"], [end_date.isoformat(), "0.0200"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.USD,
                    "pixels": [{"prefix": "pixel_1", "name": "test"}],
                },
                "success": True,
            },
        )

        mock_query.return_value = copy.deepcopy(mock_stats)
        response = self.client.get(
            reverse("account_publishers_daily_stats", kwargs={"account_id": 2}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0200"], [end_date.isoformat(), "0.0400"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.EUR,
                },
                "success": True,
            },
        )


@patch("stats.api_dailystats.query")
class AccountPlacementsDailyStatsTestCase(BaseTestCase):
    fixtures = ["test_views"]

    def setUp(self):
        password = "secret"
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [
            {"day": start_date.isoformat(), "etfm_cpc": "0.0100", "local_etfm_cpc": "0.0200", "clicks": 1000},
            {"day": end_date.isoformat(), "etfm_cpc": "0.0200", "local_etfm_cpc": "0.0400", "clicks": 1500},
        ]

        params = {
            "metrics": ["etfm_cpc", "clicks"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "totals": "true",
        }

        mock_query.return_value = copy.deepcopy(mock_stats)
        response = self.client.get(
            reverse("account_placements_daily_stats", kwargs={"account_id": 1}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0100"], [end_date.isoformat(), "0.0200"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.USD,
                    "pixels": [{"prefix": "pixel_1", "name": "test"}],
                },
                "success": True,
            },
        )

        mock_query.return_value = copy.deepcopy(mock_stats)
        response = self.client.get(
            reverse("account_placements_daily_stats", kwargs={"account_id": 2}), params, follow=True
        )

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0200"], [end_date.isoformat(), "0.0400"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.EUR,
                },
                "success": True,
            },
        )


@patch("stats.api_dailystats.query")
class AllAccountsPublishersDailyStatsTestCase(BaseTestCase):
    fixtures = ["test_views"]

    def setUp(self):
        password = "secret"
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [
            {"day": start_date.isoformat(), "etfm_cpc": "0.0100", "local_etfm_cpc": "0.0200", "clicks": 1000},
            {"day": end_date.isoformat(), "etfm_cpc": "0.0200", "local_etfm_cpc": "0.0400", "clicks": 1500},
        ]

        mock_query.return_value = mock_stats

        params = {
            "metrics": ["etfm_cpc", "clicks"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "totals": "true",
        }

        response = self.client.get(reverse("accounts_publishers_daily_stats"), params, follow=True)

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0100"], [end_date.isoformat(), "0.0200"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.USD,
                },
                "success": True,
            },
        )


@patch("stats.api_dailystats.query")
class AllAccountsPlacementsDailyStatsTestCase(BaseTestCase):
    fixtures = ["test_views"]

    def setUp(self):
        password = "secret"
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password=password)

    def test_get(self, mock_query):
        start_date = datetime.date(2015, 2, 1)
        end_date = datetime.date(2015, 2, 2)

        mock_stats = [
            {"day": start_date.isoformat(), "etfm_cpc": "0.0100", "local_etfm_cpc": "0.0200", "clicks": 1000},
            {"day": end_date.isoformat(), "etfm_cpc": "0.0200", "local_etfm_cpc": "0.0400", "clicks": 1500},
        ]

        mock_query.return_value = mock_stats

        params = {
            "metrics": ["etfm_cpc", "clicks"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "totals": "true",
        }

        response = self.client.get(reverse("accounts_placements_daily_stats"), params, follow=True)

        self.assertJSONEqual(
            response.content,
            {
                "data": {
                    "chart_data": [
                        {
                            "id": "totals",
                            "name": "Totals",
                            "series_data": {
                                "clicks": [[start_date.isoformat(), 1000], [end_date.isoformat(), 1500]],
                                "etfm_cpc": [[start_date.isoformat(), "0.0100"], [end_date.isoformat(), "0.0200"]],
                            },
                        }
                    ],
                    "currency": constants.Currency.USD,
                },
                "success": True,
            },
        )
