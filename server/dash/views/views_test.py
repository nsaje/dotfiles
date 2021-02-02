# -*- coding: utf-8 -*-

import datetime
import decimal
import json

import mock
from django.contrib.auth.models import Permission
from django.core import mail
from django.http.request import HttpRequest
from django.test import Client
from django.test import RequestFactory
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch

import core.features.delivery_status
import core.models.source_type.model
import demo
import zemauth.models
from dash import constants
from dash import history_helpers
from dash import models
from utils import test_helper
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission as ZemPermission
from zemauth.models import User


class AdGroupSourceSettingsTestCase(BaseTestCase):
    fixtures = ["test_models.yaml", "test_views.yaml"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password="secret")
        self.ad_group = models.AdGroup.objects.get(pk=1)
        self.ad_group.settings.update_unsafe(None, b1_sources_group_enabled=False)
        self._set_ad_group_sources_state(constants.AdGroupSettingsState.INACTIVE)

    def _set_ad_group_sources_state(self, state):
        for ags in self.ad_group.adgroupsource_set.all():
            ags.settings.update_unsafe(None, state=state)

    def _set_autopilot_state(self, autopilot_state):
        new_settings = self.ad_group.get_current_settings().copy_settings()
        new_settings.autopilot_state = autopilot_state
        new_settings.save(None)

    def _set_ad_group_end_date(self, days_delta=0):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.end_date = datetime.datetime.utcnow().date() + datetime.timedelta(days=days_delta)
        new_settings.save(None)

    @patch.object(models.AdGroupSourceSettings, "update")
    def test_put_local(self, mock_ad_group_source_settings_update):
        self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpc_cc": "0.5", "cpm": "0.5"}),
        )

        args, kwargs = mock_ad_group_source_settings_update.call_args
        self.assertIsNone(kwargs.get("cpc_cc"))
        self.assertIsNone(kwargs.get("cpm"))
        self.assertEqual(kwargs.get("local_cpc_cc"), decimal.Decimal("0.5"))
        self.assertEqual(kwargs.get("local_cpm"), decimal.Decimal("0.5"))

    @patch("utils.k1_helper.update_ad_group")
    def test_put_cpc_bidding_type(self, mock_k1_ping):
        self.ad_group.bidding_type = constants.BiddingType.CPC
        self.ad_group.save(None)

        response = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpm": "2.0"}),
        )
        self.assertEqual(response.status_code, 400)

    @patch("utils.k1_helper.update_ad_group")
    def test_put_cpm_bidding_type(self, mock_k1_ping):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        response = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpc_cc": "2.0"}),
        )
        self.assertEqual(response.status_code, 400)

    @patch("utils.k1_helper.update_ad_group")
    def test_logs_user_action(self, mock_k1_ping):
        self._set_ad_group_end_date(days_delta=0)
        response = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpc_cc": "0.15"}),
        )
        self.assertEqual(response.status_code, 200)
        mock_k1_ping.assert_called_with(models.AdGroup.objects.get(pk=1), "AdGroupSource.update")

        hist = (
            history_helpers.get_ad_group_history(models.AdGroup.objects.get(pk=1))
            .exclude(action_type=constants.HistoryActionType.BID_MODIFIER_UPDATE)
            .first()
        )
        self.assertEqual(constants.HistoryActionType.SETTINGS_CHANGE, hist.action_type)

    def test_source_cpc_equal_ad_group_maximum(self):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpc_cc": "1.00"}),
        )
        self.assertEqual(response.status_code, 200)

    def test_source_cpm_over_ad_group_maximum(self):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpm": "1.70"}),
        )
        self.assertEqual(response.status_code, 400)

    def test_source_cpm_equal_ad_group_maximum(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpm": "1.60"}),
        )
        self.assertEqual(response.status_code, 200)

    @patch.object(core.models.source_type.model.SourceType, "get_etfm_max_daily_budget", return_value=89.77)
    @patch.object(core.models.source_type.model.SourceType, "get_etfm_min_daily_budget", return_value=7.11)
    @patch.object(core.models.source_type.model.SourceType, "get_min_cpc", return_value=0.1211)
    def test_adgroups_sources_cpc_daily_budget_rounding(
        self, min_cpc_mock, min_daily_budget_mock, max_daily_budget_mock
    ):
        self.ad_group.settings.update_unsafe(None, cpc=0.7792)

        # min cpc - would return 0.12 without rounding ceiling
        r = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpc_cc": "0.1200"}),
        )
        json_data = json.loads(r.content)["data"]
        self.assertEqual(json_data["error_code"], "ValidationError")
        self.assertTrue("0.13" in json_data["errors"]["cpc_cc"][0])

        # min daily budget - would return 7 without rounding ceiling
        r = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpc_cc": "0.14", "daily_budget_cc": "7"}),
        )
        json_data = json.loads(r.content)["data"]
        self.assertEqual(json_data["error_code"], "ValidationError")
        self.assertTrue("8" in json_data["errors"]["daily_budget_cc"][0])

        # max daily budget - would return 90 without rounding floor
        r = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpc_cc": "0.14", "daily_budget_cc": "90"}),
        )
        json_data = json.loads(r.content)["data"]
        self.assertEqual(json_data["error_code"], "ValidationError")
        self.assertTrue("89" in json_data["errors"]["daily_budget_cc"][0])

    @patch.object(core.models.source_type.model.SourceType, "get_min_cpm", return_value=0.1211)
    def test_adgroups_sources_rounding(self, min_cpm_mock):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)
        self.ad_group.settings.update_unsafe(None, cpm=0.7792)

        # min cpm - would return 0.12 without rounding ceiling
        r = self.client.put(
            reverse("ad_group_source_settings", kwargs={"ad_group_id": "1", "source_id": "1"}),
            data=json.dumps({"cpm": "0.1200"}),
        )
        json_data = json.loads(r.content)["data"]
        self.assertEqual(json_data["error_code"], "ValidationError")
        self.assertTrue("0.13" in json_data["errors"]["cpm"][0])


class AdGroupSourcesTestCase(BaseTestCase):
    fixtures = ["test_api", "test_views"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.email, password="secret")

    def test_get_name(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = magic_mixer.blend(models.Account, name="Account š name that is toooooooo long")

        campaign = models.Campaign(name="Campaign š name that is toooooooo long", account=account)
        campaign.save(request)

        source = models.Source(name="Outbrain")
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(id=123, name="Ad group š name that is toooooooo long", campaign=campaign),
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, "ONE: Account š name that is / Campaign š name that / Ad group š name that / 123 / Outbrain"
        )

    def test_get_name_long_first_word(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = magic_mixer.blend(models.Account, name="Accountšnamethatistoooooooolong")

        campaign = models.Campaign(name="Campaignšnamethatistoooooooolong", account=account)
        campaign.save(request)

        source = models.Source(name="Outbrain")
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source, ad_group=models.AdGroup(id=123, name="Adgroupšnamethatistoooooooolong", campaign=campaign)
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, "ONE: Accountšnamethatistooo / Campaignšnamethatistoo / Adgroupšnamethatistooo / 123 / Outbrain"
        )

    def test_get_name_empty_strings(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = magic_mixer.blend(models.Account, name="")

        campaign = models.Campaign(name="", account=account)
        campaign.save(request)

        source = models.Source(name="Outbrain")
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source, ad_group=models.AdGroup(id=123, name="", campaign=campaign)
        )

        name = ad_group_source.get_external_name()

        self.assertEqual(name, "ONE:  /  /  / 123 / Outbrain")

    def test_available_sources(self):
        response = self.client.get(reverse("ad_group_sources", kwargs={"ad_group_id": 1}), follow=True)
        # Expected sources - 9 (Sharethrough)
        # Allowed sources 1-9, Sources 1-7 already added, 8 has no default setting

        response_dict = json.loads(response.content)
        self.assertEqual(len(response_dict["data"]["sources"]), 1)
        self.assertEqual(response_dict["data"]["sources"][0]["id"], 9)

    def test_available_sources_with_filter(self):
        response = self.client.get(
            reverse("ad_group_sources", kwargs={"ad_group_id": 1}), {"filtered_sources": "7,8,9"}, follow=True
        )
        # Expected sources - 9 (Sharethrough)
        # Allowed sources 1-9, Sources 1-7 already added, 8 has no default setting
        response_dict = json.loads(response.content)
        self.assertEqual(len(response_dict["data"]["sources"]), 1)
        self.assertEqual(response_dict["data"]["sources"][0]["id"], 9)

    def test_available_sources_with_filter_empty(self):
        response = self.client.get(
            reverse("ad_group_sources", kwargs={"ad_group_id": 1}), {"filtered_sources": "7,8"}, follow=True
        )
        # Expected sources - none
        # Allowed sources 1-9, Sources 1-7 already added, 8 has no default setting
        response_dict = json.loads(response.content)
        self.assertEqual(len(response_dict["data"]["sources"]), 0)

    def test_put(self):
        response = self.client.put(
            reverse("ad_group_sources", kwargs={"ad_group_id": "1"}), data=json.dumps({"source_id": "9"})
        )
        self.assertEqual(response.status_code, 200)

        ad_group = models.AdGroup.objects.get(pk=1)
        source = models.Source.objects.get(pk=9)
        ad_group_sources = ad_group.sources.all()
        self.assertIn(source, ad_group_sources)

    def test_put_overwrite_cpc(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        new_settings = ad_group.get_current_settings().copy_settings()
        new_settings.cpc = decimal.Decimal("0.1")
        new_settings.save(None)

        response = self.client.put(
            reverse("ad_group_sources", kwargs={"ad_group_id": "1"}), data=json.dumps({"source_id": "9"})
        )
        self.assertEqual(response.status_code, 200)

        source = models.Source.objects.get(pk=9)
        ad_group_sources = ad_group.sources.all()
        self.assertIn(source, ad_group_sources)

    @override_settings(K1_CONSISTENCY_SYNC=True)
    def test_put_add_content_ad_sources(self):
        response = self.client.put(
            reverse("ad_group_sources", kwargs={"ad_group_id": "1"}), data=json.dumps({"source_id": "9"})
        )
        self.assertEqual(response.status_code, 200)

        ad_group = models.AdGroup.objects.get(pk=1)
        source = models.Source.objects.get(pk=9)
        ad_group_sources = ad_group.sources.all()
        self.assertIn(source, ad_group_sources)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group)
        content_ad_sources = models.ContentAdSource.objects.filter(content_ad__ad_group=ad_group, source=source)
        self.assertTrue(content_ad_sources.exists())
        self.assertEqual(len(content_ads), len(content_ad_sources))

    def test_put_existing_source(self):
        response = self.client.put(
            reverse("ad_group_sources", kwargs={"ad_group_id": "1"}), data=json.dumps({"source_id": "1"})
        )
        self.assertEqual(response.status_code, 400)


class AdGroupOverviewTestCase(BaseTestCase):
    fixtures = ["test_api.yaml", "users"]

    def setUp(self):
        self.client = Client()
        self.user = zemauth.models.User.objects.get(pk=2)

    def _get_ad_group_overview(self, ad_group_id, with_status=False):
        self.client.login(username=self.user.username, password="secret")
        reversed_url = reverse("ad_group_overview", kwargs={"ad_group_id": ad_group_id})

        response = self.client.get(reversed_url, {"start_date": "2019-01-01", "end_date": "2019-02-01"}, follow=True)
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        ret = [s for s in settings if name in s["name"].lower()]
        if ret != []:
            return ret[0]
        else:
            return None

    @patch("redshiftapi.api_breakdowns.query")
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_run_empty(self, mock_query):
        mock_query.return_value = [
            {
                "adgroup_id": 1,
                "source_id": 9,
                "local_yesterday_at_cost": decimal.Decimal("0.0"),
                "local_yesterday_etfm_cost": decimal.Decimal("0.0"),
            }
        ]

        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_settings = ad_group.get_current_settings()
        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.local_cpc = new_ad_group_settings.cpc
        new_ad_group_settings.save(None)
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()

        credit = models.CreditLineItem.objects.create_unsafe(
            account=ad_group.campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.user,
        )

        models.BudgetLineItem.objects.create_unsafe(
            campaign=ad_group.campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=self.user,
        )

        new_settings = ad_group.get_current_settings().copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE
        new_settings.save(None)

        new_settings = ad_group.adgroupsource_set.filter(id=1)[0].get_current_settings().copy_settings()
        new_settings.state = constants.AdGroupSourceSettingsState.ACTIVE
        new_settings.save(None)

        response = self._get_ad_group_overview(1)

        self.assertTrue(response["success"])
        header = response["data"]["header"]
        self.assertEqual(header["title"], "test adgroup 1 Čžš")
        self.assertEqual(core.features.delivery_status.DetailedDeliveryStatus.INACTIVE, header["active"])

        settings = response["data"]["basic_settings"] + response["data"]["performance_settings"]
        flight_setting = self._get_setting(settings, "flight")
        self.assertEqual("-", flight_setting["value"])

        budget_setting = self._get_setting(settings, "campaign budget")
        self.assertIsNone(budget_setting, "no permission")

        pacing_setting = self._get_setting(settings, "pacing")
        self.assertIsNone(pacing_setting, "no permission")

        goal_setting = [s for s in settings if "goal" in s["name"].lower()]
        self.assertEqual([], goal_setting)

        yesterday_spend_setting = self._get_setting(settings, "yesterday spend")
        self.assertEqual("$0.00", yesterday_spend_setting["value"])

        yesterday_data_setting = self._get_setting(settings, "yesterday data")
        self.assertEqual("Complete", yesterday_data_setting["flag"])

    @patch("redshiftapi.api_breakdowns.query")
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_run_mid(self, mock_query):
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()

        # check values for adgroup that is in the middle of flight time
        # and is overperforming
        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_settings = ad_group.get_current_settings()
        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.start_date = start_date
        new_ad_group_settings.end_date = end_date
        new_ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE
        new_ad_group_settings.local_cpc = new_ad_group_settings.cpc
        new_ad_group_settings.save(None)

        new_settings = ad_group.adgroupsource_set.filter(id=1)[0].get_current_settings().copy_settings()
        new_settings.state = constants.AdGroupSourceSettingsState.ACTIVE
        new_settings.save(None)

        credit = models.CreditLineItem.objects.create_unsafe(
            account=ad_group.campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.user,
        )

        budget = models.BudgetLineItem.objects.create_unsafe(
            campaign=ad_group.campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=self.user,
        )

        models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=datetime.datetime.today() - datetime.timedelta(days=1),
            base_media_spend_nano=60 * 10 ** 9,
            base_data_spend_nano=0,
            media_spend_nano=100 * 10 ** 9,
            data_spend_nano=100 * 10 ** 9,
            service_fee_nano=0,
            license_fee_nano=0,
            margin_nano=0,
        )

        mock_query.return_value = [
            {"local_yesterday_at_cost": decimal.Decimal("60.0"), "local_yesterday_etfm_cost": decimal.Decimal("60.0")}
        ]

        response = self._get_ad_group_overview(1)

        self.assertTrue(response["success"])
        header = response["data"]["header"]
        self.assertEqual(header["title"], "test adgroup 1 Čžš")
        self.assertEqual(core.features.delivery_status.DetailedDeliveryStatus.OPTIMAL_BID, header["active"])

        settings = response["data"]["basic_settings"] + response["data"]["performance_settings"]

        flight_setting = self._get_setting(settings, "flight")
        self.assertEqual(
            "{sm}/{sd} - {em}/{ed}".format(
                sm="{:02d}".format(start_date.month),
                sd="{:02d}".format(start_date.day),
                em="{:02d}".format(end_date.month),
                ed="{:02d}".format(end_date.day),
            ),
            flight_setting["value"],
        )

        response = self._get_ad_group_overview(1)
        settings = response["data"]["basic_settings"] + response["data"]["performance_settings"]

        yesterday_spend_setting = self._get_setting(settings, "yesterday spend")
        self.assertEqual("$60.00", yesterday_spend_setting["value"])
        self.assertEqual("12.00% of $500.00 Daily Spend Cap", yesterday_spend_setting["description"])

        yesterday_data_setting = self._get_setting(settings, "yesterday data")
        self.assertEqual("Complete", yesterday_data_setting["flag"])


class CampaignOverviewTestCase(BaseTestCase):
    fixtures = ["test_api", "users"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=2)

    def _get_campaign_overview(self, campaign_id, user_id=2, with_status=False):
        self.client.login(username=self.user.username, password="secret")
        reversed_url = reverse("campaign_overview", kwargs={"campaign_id": campaign_id})
        response = self.client.get(reversed_url, {"start_date": "2019-01-01", "end_date": "2019-02-01"}, follow=True)
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        matching_settings = [s for s in settings if name in s["name"].lower()]
        if matching_settings:
            return matching_settings[0]
        return None

    @patch("redshiftapi.api_breakdowns.query")
    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    def test_run_empty(self, mock_query):
        mock_query.return_value = [
            {
                "campaign_id": 1,
                "source_id": 9,
                "local_yesterday_at_cost": decimal.Decimal("0.0"),
                "local_yesterday_etfm_cost": decimal.Decimal("0.0"),
            }
        ]
        req = RequestFactory().get("/")
        req.user = self.user

        adg_start_date = datetime.datetime.now() - datetime.timedelta(days=1)
        adg_end_date = datetime.datetime.now() + datetime.timedelta(days=1)

        # make all adgroups active
        for adgs in models.AdGroupSettings.objects.all():
            new_adgs = adgs.copy_settings()
            new_adgs.start_date = adg_start_date
            new_adgs.end_date = adg_end_date
            new_adgs.state = constants.AdGroupSettingsState.ACTIVE
            new_adgs.save(req)

        # make all adgroup sources active
        for adgss in models.AdGroupSourceSettings.objects.all():
            new_adgss = adgss.copy_settings()
            new_adgss.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_adgss.save(req)

        campaign = models.Campaign.objects.get(pk=1)
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()

        credit = models.CreditLineItem.objects.create_unsafe(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.user,
        )

        models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign, credit=credit, amount=100, start_date=start_date, end_date=end_date, created_by=self.user
        )

        response = self._get_campaign_overview(1)
        self.assertTrue(response["success"])

        header = response["data"]["header"]
        self.assertEqual("test campaign 1 \u010c\u017e\u0161", header["title"])
        self.assertEqual(core.features.delivery_status.DetailedDeliveryStatus.ACTIVE, header["active"])

        settings = response["data"]["basic_settings"] + response["data"]["performance_settings"]

        goal_setting = [s for s in settings if "goal" in s["name"].lower()]
        self.assertEqual([], goal_setting)

        response = self._get_campaign_overview(1)
        settings = response["data"]["basic_settings"] + response["data"]["performance_settings"]

        budget_setting = self._get_setting(settings, "campaign budget")
        self.assertEqual("$100.00", budget_setting["value"])
        self.assertEqual("$100.00 remaining", budget_setting["description"])

        yesterday_data_setting = self._get_setting(settings, "yesterday data")
        self.assertEqual("Complete", yesterday_data_setting["flag"])

        pacing_settings = self._get_setting(settings, "pacing")
        self.assertEqual(len(pacing_settings["children"]), 3)
        for pacing_setting in pacing_settings["children"]:
            self.assertEqual("$0.00", pacing_setting["value"])
            self.assertEqual("0.00% on plan", pacing_setting["description"])


class AccountOverviewTestCase(BaseTestCase):
    fixtures = ["test_api.yaml"]

    def setUp(self):
        self.client = Client()
        self.user = zemauth.models.User.objects.get(pk=2)

    def _get_account_overview(self, account_id, user_id=2, with_status=False):
        user = User.objects.get(pk=user_id)
        self.client.login(username=user.username, password="secret")
        reversed_url = reverse("account_overview", kwargs={"account_id": account_id})
        response = self.client.get(reversed_url, {"start_date": "2019-01-01", "end_date": "2019-02-01"}, follow=True)
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        return [s for s in settings if name in s["name"].lower()][0]

    @patch("dash.infobox_helpers.get_yesterday_account_spend")
    @patch("dash.models.Account.get_current_settings")
    def test_run_empty(self, mock_current_settings, mock_query):
        req = RequestFactory().get("/")
        req.user = self.user

        mock_query.return_value = {"yesterday_at_cost": 20, "yesterday_etfm_cost": 30}

        # make all adgroups active
        for adgs in models.AdGroupSettings.objects.all():
            new_adgs = adgs.copy_settings()
            new_adgs.start_date = datetime.datetime.now() - datetime.timedelta(days=1)
            new_adgs.end_date = datetime.datetime.now() + datetime.timedelta(days=1)
            new_adgs.state = constants.AdGroupSettingsState.ACTIVE
            new_adgs.save(req)

        # make all adgroup sources active
        for adgss in models.AdGroupSourceSettings.objects.all():
            new_adgss = adgss.copy_settings()
            new_adgss.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_adgss.save(req)

        settings = models.AccountSettings(
            default_account_manager=zemauth.models.User.objects.get(pk=1),
            default_sales_representative=zemauth.models.User.objects.get(pk=2),
        )

        mock_current_settings.return_value = settings

        response = self._get_account_overview(1)
        self.assertTrue(response["success"])

        settings = response["data"]["basic_settings"]

    @patch("dash.infobox_helpers.get_yesterday_account_spend")
    @patch("dash.models.Account.get_current_settings")
    def test_run_empty_non_archived(self, mock_current_settings, mock_query):
        req = RequestFactory().get("/")
        req.user = self.user

        mock_query.return_value = {"yesterday_at_cost": 20, "yesterday_etfm_cost": 30}

        # make all adgroups active
        for adgs in models.AdGroupSettings.objects.all():
            new_adgs = adgs.copy_settings()
            new_adgs.start_date = datetime.datetime.now() - datetime.timedelta(days=1)
            new_adgs.end_date = datetime.datetime.now() + datetime.timedelta(days=1)
            new_adgs.state = constants.AdGroupSettingsState.ACTIVE
            new_adgs.save(req)

        # make all adgroup sources active
        for adgss in models.AdGroupSourceSettings.objects.all():
            new_adgss = adgss.copy_settings()
            new_adgss.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_adgss.save(req)
        settings = models.AccountSettings(
            default_account_manager=zemauth.models.User.objects.get(pk=1),
            default_sales_representative=zemauth.models.User.objects.get(pk=2),
        )

        mock_current_settings.return_value = settings

        campaign_settings = models.Campaign.objects.get(pk=1).get_current_settings()
        new_campaign_settings = campaign_settings.copy_settings()
        new_campaign_settings.archived = True
        new_campaign_settings.save(req)

        adgroup_settings = models.AdGroup.objects.get(pk=1).get_current_settings()
        new_adgroup_settings = adgroup_settings.copy_settings()
        new_adgroup_settings.archived = True
        new_adgroup_settings.save(req)

        # do some extra setup to the account
        response = self._get_account_overview(1)
        settings = response["data"]["basic_settings"]


class AllAccountsOverviewTestCase(BaseTestCase):
    fixtures = ["test_api.yaml"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=2)
        self.client.login(username=self.user.username, password="secret")

    def _get_all_accounts_overview(self, campaign_id, with_status=False):
        reversed_url = reverse("all_accounts_overview", kwargs={})
        response = self.client.get(reversed_url, {"start_date": "2019-01-01", "end_date": "2019-02-01"}, follow=True)
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        ret = [s for s in settings if name in s["name"].lower()]
        if ret != []:
            return ret[0]
        else:
            return None

    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    @patch("dash.infobox_helpers.get_mtd_accounts_spend")
    @patch("dash.infobox_helpers.get_yesterday_accounts_spend")
    def test_run_empty(self, mock_query_yd, mock_query_mtd):
        mock_query_yd.return_value = {"yesterday_at_cost": 20, "yesterday_etfm_cost": 30}
        mock_query_mtd.return_value = {"e_media_cost": 10, "et_cost": 20, "etfm_cost": 30}

        user = zemauth.models.User.objects.get(pk=2)
        test_helper.add_entity_permissions(user, permissions=[ZemPermission.READ], entity=None)

        response = self._get_all_accounts_overview(1)
        self.assertTrue(response["success"])

        header = response["data"]["header"]
        self.assertEqual(header["title"], None)
        self.assertEqual(header["level"], constants.InfoboxLevel.ALL_ACCOUNTS)
        self.assertEqual(header["level_verbose"], constants.InfoboxLevel.get_text(constants.InfoboxLevel.ALL_ACCOUNTS))

        settings = response["data"]["basic_settings"] + response["data"]["performance_settings"]

        yesterday_spend_setting = self._get_setting(settings, "yesterday spend")
        self.assertEqual("$30.00", yesterday_spend_setting["value"])

        yesterday_data_setting = self._get_setting(settings, "yesterday data")
        self.assertEqual("Complete", yesterday_data_setting["flag"])

    @patch("dash.infobox_helpers.get_mtd_accounts_spend")
    @patch("dash.infobox_helpers.get_yesterday_accounts_spend")
    def test_agency_permission(self, mock_query_yd, mock_query_mtd):
        mock_query_yd.return_value = {"yesterday_at_cost": 20, "yesterday_etfm_cost": 30}
        mock_query_mtd.return_value = {"e_media_cost": 10, "et_cost": 20, "etfm_cost": 30}
        response = self._get_all_accounts_overview(1)
        self.assertTrue(response["success"])

        self.assertEqual(set(["Active accounts:"]), set(s["name"] for s in response["data"]["basic_settings"]))

        response = self._get_all_accounts_overview(1)
        self.assertTrue(response["success"])

        self.assertEqual(set(["Active accounts:"]), set(s["name"] for s in response["data"]["basic_settings"]))


class DemoTest(TestCase):
    fixtures = ["test_api.yaml"]

    def _get_client(self, has_permission=True):
        user = User.objects.get(pk=2)
        if has_permission:
            permission = Permission.objects.get(codename="can_request_demo_v3")
            user.user_permissions.add(permission)
            user.save()

        client = Client()
        client.login(username=user.username, password="secret")
        return client

    @patch.object(demo, "request_demo")
    def test_get(self, start_instance_mock):
        start_instance_mock.return_value = "test-name", "test-url", "test-password"

        reversed_url = reverse("demov3")
        response = self._get_client().get(reversed_url, follow=True)
        self.assertEqual(200, response.status_code)

        start_instance_mock.assert_called_once_with()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["mad.max@zemanta.com"])
        self.assertEqual(mail.outbox[0].subject, "Demo is running")
        self.assertEqual(
            mail.outbox[0].body,
            "Hi,\n\nDemo is running.\nLog in to test-url\nu/p: regular.user+demo@zemanta.com / test-password\n\nNote: This instance will selfdestroy in 7 days\n\nYours truly,\nZemanta\n    ",
        )

        data = json.loads(response.content)
        self.assertEqual({"data": {"url": "test-url", "password": "test-password"}, "success": True}, data)

    def test_get_permission(self):
        reversed_url = reverse("demov3")
        response = self._get_client(has_permission=False).get(reversed_url, follow=True)
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, "404.html")


class PushMetrics(TestCase):
    def setUp(self):
        magic_mixer.blend(core.models.AdGroup, pk=1000, custom_flags=None)
        user = magic_mixer.blend(zemauth.models.User, pk=500, username="bres@test.com", email="bres@test.com")
        user.set_password("12345")
        permission = Permission.objects.get(codename="can_enable_push_metrics")
        user.user_permissions.add(permission)
        user.save()
        self.user = user
        self.client = Client()
        self.client.login(username="bres@test.com", password="12345")

    def _toggle(self, switch):
        url = reverse("push_metrics", kwargs={"ad_group_id": "1000", "switch": switch})
        self.client.get(url)
        ad_group = models.AdGroup.objects.get(pk=1000)
        response = self.client.get(url)
        return {
            "push_metrics": ad_group.custom_flags["b1_push_metrics"],
            "response": response,
            "timestamp": response.url.split("_toggle=")[1],
        }

    def test_toggle_push_metrics(self):
        self.assertTrue(self._toggle("enable")["push_metrics"])
        self.assertFalse(self._toggle("disable")["push_metrics"])

    def test_toggle_redirect(self):
        toggle_enable = self._toggle("enable")
        self.assertRedirects(
            toggle_enable["response"],
            f"https://redash-zemanta.outbrain.com/dashboard/wizard?p_ad_group_id=1000&p_w643_toggle={toggle_enable['timestamp']}",
            fetch_redirect_response=False,
        )
        toggle_disable = self._toggle("disable")
        self.assertRedirects(
            toggle_disable["response"],
            f"https://redash-zemanta.outbrain.com/dashboard/wizard?p_ad_group_id=1000&p_w643_toggle={toggle_disable['timestamp']}",
            fetch_redirect_response=False,
        )

    def test_permission(self):
        permission = Permission.objects.get(codename="can_enable_push_metrics")
        self.user.user_permissions.remove(permission)
        self.user.save()
        url = reverse("push_metrics", kwargs={"ad_group_id": "1000", "switch": "enable"})
        response = self.client.get(url)
        self.assertEqual(401, response.status_code)
