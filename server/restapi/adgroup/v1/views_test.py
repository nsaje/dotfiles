import datetime
import json
import string
from decimal import Decimal

import mock
from django.urls import reverse

import core.features.audiences
import core.features.publisher_groups
import core.models
import dash.features.bluekai
import dash.models
import restapi.serializers
import restapi.serializers.targeting
import utils.test_helper
from automation import autopilot
from dash import constants
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class AdGroupViewSetTest(RESTAPITestCase):

    expected_none_date_output = None
    expected_none_decimal_output = ""
    expected_none_click_output = None
    expected_none_frequency_capping_output = None

    def adgroup_repr(
        cls,
        id=None,
        campaign_id=None,
        name="My test ad group",
        bidding_type=constants.BiddingType.CPC,
        bid="0.600",
        state=constants.AdGroupSettingsState.INACTIVE,
        archived=False,
        start_date=datetime.date.today(),
        end_date=None,
        max_cpc="0.600",
        max_cpm=None,
        daily_budget="50.00",
        tracking_code="a=b",
        target_regions={},
        exclusion_target_regions={},
        target_devices=[constants.AdTargetDevice.DESKTOP],
        target_environments=[constants.AdTargetEnvironment.APP],
        target_os=[{"name": constants.OperatingSystem.ANDROID}],
        target_browsers=[],
        exclusion_target_browsers=[],
        target_connection_types=[constants.ConnectionType.WIFI],
        interest_targeting=[constants.InterestCategory.WOMEN, constants.InterestCategory.FASHION],
        exclusion_interest_targeting=[constants.InterestCategory.POLITICS],
        demographic_targeting=[],
        autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        autopilot_daily_budget="50.00",
        max_autopilot_bid="0.600",
        dayparting={},
        whitelist_publisher_groups=[],
        blacklist_publisher_groups=[],
        audience_targeting=[],
        exclusion_audience_targeting=[],
        retargeting_ad_groups=[],
        exclusion_retargeting_ad_groups=[],
        delivery_type=constants.AdGroupDeliveryType.STANDARD,
        click_capping_daily_ad_group_max_clicks=120,
        click_capping_daily_click_budget="12.0000",
        frequency_capping=None,
        language_targeting_enabled=False,
    ):
        final_target_regions = {"countries": [], "regions": [], "dma": [], "cities": [], "postalCodes": []}
        final_target_regions.update(target_regions)
        final_exclusion_target_regions = {"countries": [], "regions": [], "dma": [], "cities": [], "postalCodes": []}
        final_exclusion_target_regions.update(exclusion_target_regions)
        representation = {
            "id": str(id) if id is not None else None,
            "campaignId": str(campaign_id) if campaign_id is not None else None,
            "name": name,
            "biddingType": constants.BiddingType.get_name(bidding_type),
            "bid": Decimal(bid).quantize(Decimal("1.000")),
            "state": constants.AdGroupSettingsState.get_name(state),
            "archived": archived,
            "startDate": start_date,
            "endDate": end_date if end_date else cls.expected_none_date_output,
            "maxCpc": Decimal(max_cpc).quantize(Decimal("1.000"))
            if max_cpc and max_cpm is None
            else cls.expected_none_decimal_output,
            "maxCpm": Decimal(max_cpm).quantize(Decimal("1.000")) if max_cpm else cls.expected_none_decimal_output,
            "dailyBudget": Decimal(daily_budget).quantize(Decimal("1.00"))
            if daily_budget not in (None, "")
            else cls.expected_none_decimal_output,
            "trackingCode": tracking_code,
            "targeting": {
                "geo": {"included": final_target_regions, "excluded": final_exclusion_target_regions},
                "devices": restapi.serializers.targeting.DevicesSerializer(target_devices).data,
                "environments": restapi.serializers.targeting.EnvironmentsSerializer(target_environments).data,
                "os": restapi.serializers.targeting.OSsSerializer(target_os).data,
                "browsers": restapi.adgroup.v1.serializers.BrowsersSerializer(
                    {"included": target_browsers, "excluded": exclusion_target_browsers}
                ).data,
                "browsersOen": restapi.serializers.targeting.BrowsersSerializer(target_browsers).data,
                "interest": {
                    "included": [constants.InterestCategory.get_name(i) for i in interest_targeting],
                    "excluded": [constants.InterestCategory.get_name(i) for i in exclusion_interest_targeting],
                },
                "audience": restapi.serializers.targeting.AudienceSerializer(demographic_targeting).data,
                "publisherGroups": {"included": whitelist_publisher_groups, "excluded": blacklist_publisher_groups},
                "customAudiences": {"included": audience_targeting, "excluded": exclusion_audience_targeting},
                "retargetingAdGroups": {"included": retargeting_ad_groups, "excluded": exclusion_retargeting_ad_groups},
                "language": {"matchingEnabled": language_targeting_enabled},
                "connectionTypes": restapi.serializers.targeting.ConnectionTypesSerializer(
                    target_connection_types
                ).data,
            },
            "autopilot": {
                "state": constants.AdGroupSettingsAutopilotState.get_name(autopilot_state),
                "dailyBudget": Decimal(autopilot_daily_budget).quantize(Decimal("1.00"))
                if autopilot_daily_budget not in (None, "")
                else cls.expected_none_decimal_output,
                "maxBid": Decimal(max_autopilot_bid).quantize(Decimal("1.000"))
                if max_autopilot_bid
                else cls.expected_none_decimal_output,
            },
            "dayparting": dayparting,
            "deliveryType": constants.AdGroupDeliveryType.get_name(delivery_type),
            "clickCappingDailyAdGroupMaxClicks": click_capping_daily_ad_group_max_clicks
            if click_capping_daily_ad_group_max_clicks
            else cls.expected_none_click_output,
            "clickCappingDailyClickBudget": click_capping_daily_click_budget
            if click_capping_daily_click_budget
            else cls.expected_none_click_output,
            "frequencyCapping": frequency_capping if frequency_capping else cls.expected_none_frequency_capping_output,
        }
        return cls.normalize(representation)

    @staticmethod
    def _partition_regions(target_regions):
        """ non-exact heuristics in order to not reimplement functionality in tests """
        geo = {"countries": [], "regions": [], "dma": [], "cities": [], "postalCodes": []}
        for tr in target_regions:
            if len(tr) == 2 and all(char in string.ascii_uppercase for char in tr):
                geo["countries"].append(tr)
            elif 5 <= len(tr) <= 6 and "-" in tr:
                geo["regions"].append(tr)
            elif ":" in tr:
                geo["postalCodes"].append(tr)
            elif len(tr) == 3:
                geo["dma"].append(tr)
            else:
                geo["cities"].append(int(tr))
        return geo

    def validate_against_db(self, adgroup):
        adgroup_db = dash.models.AdGroup.objects.get(pk=adgroup["id"])
        settings_db = adgroup_db.get_current_settings()
        expected = self.adgroup_repr(
            id=adgroup_db.id,
            campaign_id=adgroup_db.campaign_id,
            name=settings_db.ad_group_name,
            bidding_type=settings_db.ad_group.bidding_type,
            bid=settings_db.local_bid,
            state=settings_db.state,
            archived=settings_db.archived,
            start_date=settings_db.start_date,
            end_date=settings_db.end_date,
            max_cpc=settings_db.max_cpc_legacy,
            max_cpm=settings_db.max_cpm_legacy,
            daily_budget=settings_db.daily_budget_legacy,
            tracking_code=settings_db.tracking_code,
            target_regions=self._partition_regions(settings_db.target_regions),
            interest_targeting=settings_db.interest_targeting,
            exclusion_interest_targeting=settings_db.exclusion_interest_targeting,
            demographic_targeting=settings_db.bluekai_targeting,
            language_targeting_enabled=settings_db.language_targeting_enabled,
            autopilot_state=settings_db.autopilot_state,
            autopilot_daily_budget=settings_db.local_autopilot_daily_budget,
            max_autopilot_bid=settings_db.max_autopilot_bid,
            dayparting=settings_db.dayparting,
            whitelist_publisher_groups=settings_db.whitelist_publisher_groups,
            blacklist_publisher_groups=settings_db.blacklist_publisher_groups,
            audience_targeting=settings_db.audience_targeting,
            exclusion_audience_targeting=settings_db.exclusion_audience_targeting,
            retargeting_ad_groups=settings_db.retargeting_ad_groups,
            exclusion_retargeting_ad_groups=settings_db.exclusion_retargeting_ad_groups,
            target_devices=settings_db.target_devices,
            target_environments=settings_db.target_environments,
            target_os=settings_db.target_os,
            target_browsers=settings_db.target_browsers,
            exclusion_target_browsers=settings_db.exclusion_target_browsers,
            target_connection_types=settings_db.target_connection_types,
            click_capping_daily_ad_group_max_clicks=settings_db.click_capping_daily_ad_group_max_clicks,
            click_capping_daily_click_budget=settings_db.click_capping_daily_click_budget,
            frequency_capping=settings_db.frequency_capping,
        )
        # TODO: PLAC: remove after legacy grace period
        expected["targeting"]["placements"] = expected["targeting"]["environments"]
        self.assertEqual(expected, adgroup)

    def test_adgroups_get_cpc(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account = self.mix_account(self.user, permissions=[Permission.READ], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertTrue(resp_json["data"]["bid"])
        self.assertTrue(resp_json["data"]["maxCpc"])
        self.assertFalse(resp_json["data"]["maxCpm"])

    def test_adgroups_get_cpm(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account = self.mix_account(self.user, permissions=[Permission.READ], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPM)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertTrue(resp_json["data"]["bid"])
        self.assertFalse(resp_json["data"]["maxCpc"])
        self.assertTrue(resp_json["data"]["maxCpm"])

    def test_adgroups_get_include_delivery_status(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPM)

        r = self.client.get(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            {"includeDeliveryStatus": "true"},
        )
        resp_json = self.assertResponseValid(r)
        self.assertIn("deliveryStatus", resp_json["data"])

    def test_adgroups_list(self):
        account = self.mix_account(self.user, permissions=[Permission.READ], agency__uses_realtime_autopilot=True)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_groups = magic_mixer.cycle(5).blend(core.models.AdGroup, campaign=campaign)

        account_no_access = magic_mixer.blend(core.models.Account)
        campaign_no_access = magic_mixer.blend(core.models.Campaign, account=account_no_access)
        magic_mixer.cycle(5).blend(core.models.AdGroup, campaign=campaign_no_access)

        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_list"))
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_ids = sorted([x.get("id") for x in resp_json["data"]])
        ad_groups_ids = sorted([str(x.id) for x in ad_groups])
        self.assertEqual(resp_json_ids, ad_groups_ids)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_adgroups_list_account_id(self):
        account_one = self.mix_account(self.user, permissions=[Permission.READ], agency__uses_realtime_autopilot=True)
        account_two = self.mix_account(self.user, permissions=[Permission.READ], agency__uses_realtime_autopilot=True)

        ad_groups_one = magic_mixer.cycle(5).blend(core.models.AdGroup, campaign__account=account_one)
        magic_mixer.cycle(5).blend(core.models.AdGroup, account=account_two)

        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_list"), data={"accountId": account_one.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_ids = sorted([x.get("id") for x in resp_json["data"]])
        ad_groups_one_ids = sorted([str(x.id) for x in ad_groups_one])
        self.assertEqual(resp_json_ids, ad_groups_one_ids)
        for item in resp_json["data"]:
            self.validate_against_db(item)
            db_item = core.models.AdGroup.objects.get(pk=item["id"])
            self.assertEqual(db_item.campaign.account_id, account_one.id)

    def test_adgroups_list_campaign_id(self):
        account = self.mix_account(self.user, permissions=[Permission.READ], agency__uses_realtime_autopilot=True)

        campaign_one = magic_mixer.blend(core.models.Campaign, account=account)
        ad_groups_one = magic_mixer.cycle(5).blend(core.models.AdGroup, campaign=campaign_one)

        campaign_two = magic_mixer.blend(core.models.Campaign, account=account)
        magic_mixer.cycle(5).blend(core.models.AdGroup, campaign=campaign_two)

        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_list"), data={"campaignId": campaign_one.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_ids = sorted([x.get("id") for x in resp_json["data"]])
        ad_groups_one_ids = sorted([str(x.id) for x in ad_groups_one])
        self.assertEqual(resp_json_ids, ad_groups_one_ids)
        for item in resp_json["data"]:
            self.validate_against_db(item)
            self.assertEqual(int(item["campaignId"]), campaign_one.id)

    def test_adgroups_list_include_delivery(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])

        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        magic_mixer.cycle(5).blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(
            reverse("restapi.adgroup.v1:adgroups_list"),
            data={"campaignId": campaign.id, "includeDeliveryStatus": "true"},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(5, len(resp_json["data"]))
        for item in resp_json["data"]:
            self.assertTrue(item["deliveryStatus"])

    def test_adgroups_campaign_id_invalid(self):
        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_list"), data={"campaignId": 1000})
        self.assertResponseError(r, "MissingDataError")
        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_list"), data={"campaignId": "NON-NUMERIC"})
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Invalid format"], resp_json["details"]["campaignId"])

    def test_adgroups_list_pagination(self):
        account = self.mix_account(self.user, permissions=[Permission.READ], agency__uses_realtime_autopilot=True)
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        magic_mixer.cycle(10).blend(dash.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_list"), {"campaignId": campaign.id})
        r_paginated = self.client.get(
            reverse("restapi.adgroup.v1:adgroups_list"), {"campaignId": campaign.id, "limit": 2, "offset": 5}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json["data"][5:7], resp_json_paginated["data"])

    def test_adgroups_list_exclude_archived(self):
        account = self.mix_account(self.user, permissions=[Permission.READ], agency__uses_realtime_autopilot=True)
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        magic_mixer.cycle(3).blend(dash.models.AdGroup, campaign=campaign, archived=False)
        magic_mixer.cycle(2).blend(dash.models.AdGroup, campaign=campaign, archived=True)

        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_list"), {"campaignId": campaign.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(3, len(resp_json["data"]))
        for item in resp_json["data"]:
            self.validate_against_db(item)
            self.assertFalse(item["archived"])

    def test_adgroups_list_include_archived(self):
        account = self.mix_account(self.user, permissions=[Permission.READ], agency__uses_realtime_autopilot=True)
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        magic_mixer.cycle(3).blend(dash.models.AdGroup, campaign=campaign, archived=False)
        magic_mixer.cycle(2).blend(dash.models.AdGroup, campaign=campaign, archived=True)

        r = self.client.get(
            reverse("restapi.adgroup.v1:adgroups_list"), {"campaignId": campaign.id, "includeArchived": 1}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(5, len(resp_json["data"]))
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_adgroups_post_cpc(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(campaign_id=campaign.id, name="Test Group")
        del new_ad_group["bid"]

        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

        new_ad_group["id"] = resp_json["data"]["id"]
        # TODO: PLAC: remove after legacy grace period
        new_ad_group["targeting"]["placements"] = new_ad_group["targeting"]["environments"]
        new_ad_group["bid"] = resp_json["data"]["maxCpc"]
        new_ad_group["dailyBudget"] = resp_json["data"]["dailyBudget"]
        new_ad_group["autopilot"]["dailyBudget"] = resp_json["data"]["dailyBudget"]
        self.assertEqual(resp_json["data"], new_ad_group)
        adgroup_db = dash.models.AdGroup.objects.get(pk=new_ad_group["id"])
        self.assertEqual(adgroup_db.name, adgroup_db.get_current_settings().ad_group_name)
        self.assertTrue(resp_json["data"]["maxCpc"])
        self.assertFalse(resp_json["data"]["maxCpm"])
        self.assertEqual("50.00", resp_json["data"]["dailyBudget"])
        self.assertEqual("50.00", resp_json["data"]["autopilot"]["dailyBudget"])

    def test_adgroups_post_bid_cpc(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(campaign_id=campaign.id, name="Test Group")
        del new_ad_group["maxCpc"]

        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

        new_ad_group["id"] = resp_json["data"]["id"]
        # TODO: PLAC: remove after legacy grace period
        new_ad_group["targeting"]["placements"] = new_ad_group["targeting"]["environments"]
        new_ad_group["maxCpc"] = resp_json["data"]["bid"]

        # RESTAPI default is b1_sources_group_enabled=False so source budgets get aggregated into daily_budget
        # but because there are no allowed/active sources it gets overwritten by zero
        new_ad_group["dailyBudget"] = resp_json["data"]["dailyBudget"]
        new_ad_group["autopilot"]["dailyBudget"] = resp_json["data"]["dailyBudget"]

        self.assertEqual(resp_json["data"], new_ad_group)
        adgroup_db = dash.models.AdGroup.objects.get(pk=new_ad_group["id"])
        self.assertEqual(adgroup_db.name, adgroup_db.get_current_settings().ad_group_name)
        self.assertTrue(resp_json["data"]["maxCpc"])
        self.assertFalse(resp_json["data"]["maxCpm"])

    def test_adgroups_post_cpc_mixed(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(
            campaign_id=campaign.id, name="Test Group", bid="9.000", max_autopilot_bid="9.000"
        )

        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

        new_ad_group["id"] = resp_json["data"]["id"]
        new_ad_group["dailyBudget"] = resp_json["data"]["dailyBudget"]
        new_ad_group["autopilot"]["dailyBudget"] = resp_json["data"]["dailyBudget"]
        # TODO: PLAC: remove after legacy grace period
        new_ad_group["targeting"]["placements"] = new_ad_group["targeting"]["environments"]
        # "bid" value overrides "maxCpc" value
        new_ad_group["maxCpc"] = new_ad_group["bid"]
        self.assertEqual(resp_json["data"], new_ad_group)
        adgroup_db = dash.models.AdGroup.objects.get(pk=new_ad_group["id"])
        self.assertEqual(adgroup_db.name, adgroup_db.get_current_settings().ad_group_name)
        self.assertTrue(resp_json["data"]["maxCpc"])
        self.assertFalse(resp_json["data"]["maxCpm"])

    def test_adgroups_post_cpm(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(
            campaign_id=campaign.id,
            name="Test Group",
            bidding_type=constants.BiddingType.CPM,
            max_cpm="3.100",
            max_autopilot_bid="3.100",
        )
        del new_ad_group["bid"]
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

        new_ad_group["id"] = resp_json["data"]["id"]
        # TODO: PLAC: remove after legacy grace period
        new_ad_group["targeting"]["placements"] = new_ad_group["targeting"]["environments"]
        new_ad_group["maxCpm"] = resp_json["data"]["maxCpm"]
        new_ad_group["bid"] = resp_json["data"]["maxCpm"]
        new_ad_group["dailyBudget"] = resp_json["data"]["dailyBudget"]
        new_ad_group["autopilot"]["dailyBudget"] = resp_json["data"]["dailyBudget"]
        self.assertEqual(resp_json["data"], new_ad_group)
        self.assertFalse(resp_json["data"]["maxCpc"])
        self.assertTrue(resp_json["data"]["maxCpm"])
        self.assertEqual("50.00", resp_json["data"]["dailyBudget"])
        self.assertEqual("50.00", resp_json["data"]["autopilot"]["dailyBudget"])

    def test_adgroups_post_bid_cpm(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(
            campaign_id=campaign.id, name="Test Group", bidding_type=constants.BiddingType.CPM, max_cpm="3.100"
        )
        del new_ad_group["maxCpm"]

        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

        new_ad_group["id"] = resp_json["data"]["id"]
        # TODO: PLAC: remove after legacy grace period
        new_ad_group["targeting"]["placements"] = new_ad_group["targeting"]["environments"]
        new_ad_group["maxCpm"] = resp_json["data"]["bid"]
        new_ad_group["dailyBudget"] = resp_json["data"]["dailyBudget"]
        new_ad_group["autopilot"]["dailyBudget"] = resp_json["data"]["dailyBudget"]
        self.assertEqual(resp_json["data"], new_ad_group)
        self.assertFalse(resp_json["data"]["maxCpc"])
        self.assertTrue(resp_json["data"]["maxCpm"])

    def test_adgroups_post_campaign_archived(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account, archived=True)
        new_ad_group = self.adgroup_repr(campaign_id=campaign.id, name="Test Group")

        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            ["Can not create an ad group on an archived campaign."], json.loads(r.content)["details"]["campaignId"]
        )

    def test_adgroups_post_no_campaign_id(self):
        new_ad_group = self.adgroup_repr(name="Test Group")
        del new_ad_group["id"]
        del new_ad_group["campaignId"]
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_post_no_state(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        new_ad_group = self.adgroup_repr(campaign_id=campaign.id, name="Test Group")
        del new_ad_group["id"]
        del new_ad_group["state"]

        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["state"], "INACTIVE")

    def test_adgroups_post_wrong_campaign_id(self):
        new_ad_group = self.adgroup_repr(campaign_id=1000, name="Test Group")
        del new_ad_group["id"]
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "MissingDataError")

    def test_adgroups_post_no_name(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        new_ad_group = self.adgroup_repr(campaign_id=campaign.id)

        del new_ad_group["id"]
        del new_ad_group["name"]
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_cpc(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        test_adgroup = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id)
        del test_adgroup["bid"]

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_adgroup,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        # TODO: PLAC: remove after legacy grace period
        test_adgroup["targeting"]["placements"] = test_adgroup["targeting"]["environments"]
        test_adgroup["bid"] = resp_json["data"]["maxCpc"]
        self.assertEqual(resp_json["data"], test_adgroup)

    def test_adgroups_put_bid_cpc(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        test_adgroup = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id)
        del test_adgroup["maxCpc"]

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_adgroup,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        # TODO: PLAC: remove after legacy grace period
        test_adgroup["targeting"]["placements"] = test_adgroup["targeting"]["environments"]
        test_adgroup["maxCpc"] = resp_json["data"]["bid"]
        self.assertEqual(resp_json["data"], test_adgroup)

    def test_adgroups_put_cpc_mixed(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        test_adgroup = self.adgroup_repr(
            id=ad_group.id, campaign_id=campaign.id, bid="9.000", max_autopilot_bid="9.000"
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_adgroup,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        # TODO: PLAC: remove after legacy grace period
        test_adgroup["targeting"]["placements"] = test_adgroup["targeting"]["environments"]
        # "bid" value overrides "maxCpc" value
        test_adgroup["maxCpc"] = test_adgroup["bid"]
        self.assertEqual(resp_json["data"], test_adgroup)

    def test_adgroups_put_cpm(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPM)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        test_adgroup = self.adgroup_repr(
            id=ad_group.id,
            campaign_id=campaign.id,
            bidding_type=constants.BiddingType.CPM,
            max_cpm="3.100",
            max_autopilot_bid="3.100",
        )
        del test_adgroup["bid"]

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_adgroup,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        # TODO: PLAC: remove after legacy grace period
        test_adgroup["targeting"]["placements"] = test_adgroup["targeting"]["environments"]
        test_adgroup["maxCpm"] = resp_json["data"]["maxCpm"]
        test_adgroup["bid"] = test_adgroup["maxCpm"]
        self.assertEqual(resp_json["data"], test_adgroup)
        self.assertFalse(resp_json["data"]["maxCpc"])
        self.assertTrue(resp_json["data"]["maxCpm"])

    def test_adgroups_put_bid_cpm(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPM)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        test_adgroup = self.adgroup_repr(
            id=ad_group.id, campaign_id=campaign.id, bidding_type=constants.BiddingType.CPM, max_cpm="3.100"
        )
        del test_adgroup["maxCpm"]

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_adgroup,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        # TODO: PLAC: remove after legacy grace period
        test_adgroup["targeting"]["placements"] = test_adgroup["targeting"]["environments"]
        test_adgroup["maxCpm"] = resp_json["data"]["bid"]
        self.assertEqual(resp_json["data"], test_adgroup)
        self.assertFalse(resp_json["data"]["maxCpc"])
        self.assertTrue(resp_json["data"]["maxCpm"])

    def test_adgroups_put_max_autopilot_bid(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        test_adgroup = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, max_autopilot_bid="18.000")
        del test_adgroup["bid"]
        del test_adgroup["maxCpc"]
        del test_adgroup["maxCpm"]

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_adgroup,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        # TODO: PLAC: remove after legacy grace period
        test_adgroup["targeting"]["placements"] = test_adgroup["targeting"]["environments"]
        test_adgroup["bid"] = resp_json["data"]["bid"]
        test_adgroup["maxCpc"] = resp_json["data"]["maxCpc"]
        test_adgroup["maxCpm"] = resp_json["data"]["maxCpm"]
        self.assertEqual(resp_json["data"], test_adgroup)

    def test_adgroups_put_daily_budget(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None,
            b1_sources_group_enabled=True,
            daily_budget_cc=Decimal("10.0"),
            local_daily_budget=Decimal("100.0"),
            local_autopilot_daily_budget=Decimal("120.0"),
        )

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, daily_budget="123.4")
        del put_data["autopilot"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        ad_group.refresh_from_db()
        self.assertEqual(Decimal("10"), ad_group.settings.daily_budget_cc)
        self.assertEqual(Decimal("123.40"), ad_group.settings.local_daily_budget)
        self.assertEqual(Decimal("123.40"), ad_group.settings.local_autopilot_daily_budget)
        self.assertEqual("123.40", resp_json["data"]["dailyBudget"])
        self.assertEqual("123.40", resp_json["data"]["autopilot"]["dailyBudget"])

    def test_adgroups_put_daily_budget_legacy_agency(self):
        account = self.mix_account(
            self.user,
            permissions=[Permission.READ, Permission.WRITE],
            agency__id=1234,
            agency__uses_realtime_autopilot=False,
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(
            None,
            b1_sources_group_enabled=True,
            daily_budget_cc=Decimal("10.0"),
            local_daily_budget=Decimal("100.0"),
            local_autopilot_daily_budget=Decimal("120.0"),
        )

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, daily_budget="123.4")
        del put_data["autopilot"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        ad_group.refresh_from_db()
        self.assertEqual(Decimal("123.40"), ad_group.settings.daily_budget_cc)
        self.assertEqual(Decimal("100.00"), ad_group.settings.local_daily_budget)
        self.assertEqual(Decimal("120.00"), ad_group.settings.local_autopilot_daily_budget)
        self.assertEqual("123.40", resp_json["data"]["dailyBudget"])
        self.assertEqual("120.00", resp_json["data"]["autopilot"]["dailyBudget"])

    def test_adgroups_put_name(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, name="New Name")
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        adgroup_db = dash.models.AdGroup.objects.get(pk=ad_group.id)
        self.assertEqual(adgroup_db.name, adgroup_db.get_current_settings().ad_group_name)

    def test_adgroups_put_frequency_capping(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, frequency_capping=33)
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["frequencyCapping"], 33)

    def test_adgroups_put_empty(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = {}
        settings_count = dash.models.AdGroupSettings.objects.filter(ad_group_id=ad_group.id).count()
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(settings_count, dash.models.AdGroupSettings.objects.filter(ad_group_id=ad_group.id).count())

    def test_adgroups_put_state(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(
            id=ad_group.id, campaign_id=campaign.id, state=constants.AdGroupSettingsState.INACTIVE
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["state"], "INACTIVE")

    def test_adgroups_put_invalid_state(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data={"state": "NOTVALID"},
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_archive_restore(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data={"archived": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["archived"], True)

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data={"archived": False},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["archived"], False)

    @mock.patch.object(autopilot, "recalculate_ad_group_budgets", autospec=True)
    def test_adgroups_put_autopilot_budget(self, mock_autopilot):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.b1_sources_group_enabled = True
        settings.save(None)

        test_adgroup = self.adgroup_repr(
            id=ad_group.id,
            campaign_id=campaign.id,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            autopilot_daily_budget="20.00",
            daily_budget="20.00",
            max_autopilot_bid="0.600",
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_adgroup,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        # TODO: PLAC: remove after legacy grace period
        test_adgroup["targeting"]["placements"] = test_adgroup["targeting"]["environments"]
        self.assertEqual(resp_json["data"], test_adgroup)

    # TODO: PLAC: remove after legacy grace period
    def test_ad_group_put_environment_targeting_legacy(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.target_environments = [dash.constants.AdTargetEnvironment.APP, dash.constants.AdTargetEnvironment.SITE]
        settings.save(None)

        self.assertEqual(
            [dash.constants.AdTargetEnvironment.APP, dash.constants.AdTargetEnvironment.SITE],
            ad_group.settings.target_environments,
        )

        ad_group_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id)
        del ad_group_data["targeting"]["environments"]
        ad_group_data["targeting"]["placements"] = ["SITE"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=ad_group_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(["SITE"], resp_json["data"]["targeting"]["environments"])
        self.assertEqual(["SITE"], resp_json["data"]["targeting"]["placements"])
        del resp_json["data"]["targeting"]["placements"]
        ad_group.refresh_from_db()
        self.assertEqual([dash.constants.AdTargetEnvironment.SITE], ad_group.settings.target_environments)

        ad_group_data = self.adgroup_repr(
            id=ad_group.id, campaign_id=campaign.id, target_environments=[constants.Environment.APP]
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=ad_group_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(["APP"], resp_json["data"]["targeting"]["environments"])
        self.assertEqual(["APP"], resp_json["data"]["targeting"]["placements"])
        del resp_json["data"]["targeting"]["placements"]
        ad_group.refresh_from_db()
        self.assertEqual([dash.constants.AdTargetEnvironment.APP], ad_group.settings.target_environments)

        ad_group_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id)
        ad_group_data["targeting"]["environments"] = ["APP"]
        ad_group_data["targeting"]["placements"] = ["SITE"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=ad_group_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(["APP"], resp_json["data"]["targeting"]["environments"])
        self.assertEqual(["APP"], resp_json["data"]["targeting"]["placements"])
        del resp_json["data"]["targeting"]["placements"]
        ad_group.refresh_from_db()
        self.assertEqual([dash.constants.AdTargetEnvironment.APP], ad_group.settings.target_environments)

        ad_group_data = self.adgroup_repr(
            id=ad_group.id, campaign_id=campaign.id, target_environments=[constants.Environment.SITE]
        )
        ad_group_data["targeting"]["placements"] = ["SITE"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=ad_group_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(["SITE"], resp_json["data"]["targeting"]["environments"])
        self.assertEqual(["SITE"], resp_json["data"]["targeting"]["placements"])
        del resp_json["data"]["targeting"]["placements"]
        ad_group.refresh_from_db()
        self.assertEqual([dash.constants.AdTargetEnvironment.SITE], ad_group.settings.target_environments)

    def test_adgroups_post_multiple_cpc_legacy_error(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(campaign_id=campaign.id, name="Test Group", max_autopilot_bid=Decimal("9000"))
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], "Bid updated with multiple values")

    def test_adgroups_post_high_cpc(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(
            campaign_id=campaign.id, name="Test Group", max_cpc=Decimal("9000"), max_autopilot_bid=Decimal("9000")
        )
        del new_ad_group["bid"]
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], {"maxCpc": ["CPC can't be higher than $20.00."]})

        new_ad_group = self.adgroup_repr(campaign_id=campaign.id, name="Test Group", bid=Decimal("9000"))
        del new_ad_group["id"]
        del new_ad_group["autopilot"]
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], {"bid": ["CPC can't be higher than $20.00."]})

    def test_adgroups_put_low_cpc(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, max_cpc="0.0")
        del put_data["bid"]
        del put_data["autopilot"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], {"maxCpc": ["CPC can't be lower than $0.005."]})

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, bid="0.0", max_autopilot_bid="0.0")
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], {"bid": ["CPC can't be lower than $0.005."]})

    def test_adgroups_post_multiple_cpm_legacy_error(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(
            campaign_id=campaign.id,
            name="Test Group",
            bidding_type=constants.BiddingType.CPM,
            max_autopilot_bid=Decimal("9000"),
        )
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], "Bid updated with multiple values")

    def test_adgroups_post_high_cpm(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(
            campaign_id=campaign.id, name="Test Group", max_cpm=Decimal("9000"), bidding_type=constants.BiddingType.CPM
        )
        del new_ad_group["bid"]
        del new_ad_group["autopilot"]
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], {"maxCpm": ["CPM can't be higher than $25.00."]})

        new_ad_group = self.adgroup_repr(
            campaign_id=campaign.id,
            name="Test Group",
            bid=Decimal("9000"),
            max_autopilot_bid=Decimal("9000"),
            bidding_type=constants.BiddingType.CPM,
        )
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], {"bid": ["CPM can't be higher than $25.00."]})

    def test_adgroups_put_low_cpm(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPM)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_cpc = Decimal("0.4500")
        settings.local_cpm = Decimal("1.2000")
        settings.save(None)

        ad_group_data = self.adgroup_repr(
            id=ad_group.id,
            campaign_id=campaign.id,
            bidding_type=constants.BiddingType.CPM,
            max_cpm="0.0",
            max_autopilot_bid="0.0",
        )
        del ad_group_data["bid"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=ad_group_data,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], {"maxCpm": ["CPM can't be lower than $0.01."]})

        ad_group_data = self.adgroup_repr(
            id=ad_group.id, campaign_id=campaign.id, bidding_type=constants.BiddingType.CPM, bid="0.0"
        )
        del ad_group_data["autopilot"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=ad_group_data,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], {"bid": ["CPM can't be lower than $0.01."]})

    def test_adgroups_post_multiple_budget_legacy_error(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(
            campaign_id=campaign.id,
            name="Test Group",
            daily_budget=Decimal("9000"),
            autopilot_daily_budget=Decimal("9001"),
        )
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], "Budget updated with multiple values")

    def test_adgroups_put_end_date_before_start_date(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(
            id=ad_group.id,
            campaign_id=campaign.id,
            start_date=datetime.date.today() + datetime.timedelta(days=10),
            end_date=datetime.date.today() + datetime.timedelta(days=7),
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_end_date_in_the_past(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(
            id=ad_group.id,
            campaign_id=campaign.id,
            start_date=datetime.date.today() + datetime.timedelta(days=10),
            end_date=datetime.date.today() + datetime.timedelta(days=7),
            state=constants.AdGroupSettingsState.ACTIVE,
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_invalid_tracking_code(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, tracking_code="_[]...")
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_post_no_targets(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)

        new_ad_group = self.adgroup_repr(campaign_id=campaign.id, name="Test Group", target_devices=[])
        del new_ad_group["id"]
        r = self.client.post(reverse("restapi.adgroup.v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_invalid_timezone(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, dayparting={"timezone": "incorrectzone"})
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_invalid_hour(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, dayparting={"friday": [0, 1, 25]})
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_invalid_bluekai_targeting(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        demographic_targeting = ["and", "bluekai:12f3", ["or", "lotame:123", "outbrain:123"]]
        put_data = self.adgroup_repr(
            id=ad_group.id, campaign_id=campaign.id, demographic_targeting=demographic_targeting
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_valid_bluekai_targeting(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        bluekai = magic_mixer.blend(
            dash.features.bluekai.BlueKaiCategory, status=dash.features.bluekai.BlueKaiCategoryStatus.ACTIVE
        )

        demographic_targeting = ["and", "bluekai:{}".format(bluekai.category_id), ["or", "lotame:123", "outbrain:123"]]
        put_data = self.adgroup_repr(
            id=ad_group.id, campaign_id=campaign.id, demographic_targeting=demographic_targeting
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(
            restapi.serializers.targeting.AudienceSerializer(demographic_targeting).data,
            resp_json["data"]["targeting"]["audience"],
        )

    def test_adgroups_invalid_regions_targeting(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        target_regions = {"countries": ["NON-VALID"]}
        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, target_regions=target_regions)
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_valid_regions_targeting(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        country = magic_mixer.blend(dash.models.Geolocation, pk="US", type="co", name="United States")

        target_regions = {"countries": [country.pk]}
        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, target_regions=target_regions)
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(country.pk, resp_json["data"]["targeting"]["geo"]["included"]["countries"][0])

    def test_adgroups_get_permissioned(self):
        account = self.mix_account(self.user, permissions=[Permission.READ], agency__uses_realtime_autopilot=True)
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        utils.test_helper.remove_permissions(self.user, permissions=["can_set_click_capping_daily_click_budget"])
        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        self.assertFalse("clickCappingDailyClickBudget" in resp_json["data"])
        resp_json["data"]["clickCappingDailyClickBudget"] = self.expected_none_click_output
        self.validate_against_db(resp_json["data"])

    def test_adgroups_put_blank_strings(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(
            id=ad_group.id,
            campaign_id=campaign.id,
            end_date="",
            tracking_code="",
            bid="1.5",
            interest_targeting=[],
            target_browsers=[],
            exclusion_target_browsers=[],
            daily_budget="",
            autopilot_daily_budget="",
            click_capping_daily_ad_group_max_clicks="",
            click_capping_daily_click_budget="",
            dayparting={"timezone": ""},
            frequency_capping="",
        )
        del put_data["maxCpc"]
        del put_data["autopilot"]["maxBid"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["endDate"], self.expected_none_date_output)
        self.assertEqual(resp_json["data"]["trackingCode"], "")
        self.assertEqual(resp_json["data"]["maxCpc"], "1.500")
        self.assertEqual(resp_json["data"]["maxCpm"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["targeting"]["interest"]["included"], [])
        self.assertEqual(resp_json["data"]["targeting"]["browsers"]["included"], [])
        self.assertEqual(resp_json["data"]["targeting"]["browsers"]["excluded"], [])
        self.assertEqual(resp_json["data"]["dailyBudget"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["autopilot"]["dailyBudget"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["clickCappingDailyAdGroupMaxClicks"], self.expected_none_click_output)
        self.assertEqual(resp_json["data"]["clickCappingDailyClickBudget"], self.expected_none_click_output)
        self.assertEqual(resp_json["data"]["dayparting"]["timezone"], "")
        self.assertEqual(resp_json["data"]["frequencyCapping"], self.expected_none_frequency_capping_output)

    def test_adgroups_put_blank_cpc(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.cpc = Decimal("1.1000")
        settings.cpm = Decimal("3.1000")
        settings.save(None)

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, bid="1.5")
        del put_data["autopilot"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["maxCpc"], "1.500")
        self.assertEqual(resp_json["data"]["maxCpm"], self.expected_none_decimal_output)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.5000"), ad_group.settings.cpc)  # blank value defaults to default cpc
        self.assertEqual(Decimal("3.1000"), ad_group.settings.cpm)

    def test_adgroups_put_blank_cpm(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPM)
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.cpc = Decimal("1.1000")
        settings.cpm = Decimal("3.1000")
        settings.save(None)

        put_data = self.adgroup_repr(
            id=ad_group.id, campaign_id=campaign.id, bid="1.5", bidding_type=constants.BiddingType.CPM
        )
        del put_data["autopilot"]
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["maxCpc"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["maxCpm"], "1.500")
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.1000"), ad_group.settings.cpc)
        self.assertEqual(Decimal("1.5000"), ad_group.settings.cpm)  # blank value defaults to default cpc

    def test_adgroups_put_none(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        put_data = self.adgroup_repr(
            id=ad_group.id,
            campaign_id=campaign.id,
            end_date=None,
            tracking_code=None,
            interest_targeting=[],
            target_browsers=None,
            exclusion_audience_targeting=None,
            daily_budget=None,
            autopilot_daily_budget=None,
            click_capping_daily_ad_group_max_clicks=None,
            click_capping_daily_click_budget=None,
            dayparting=None,
            frequency_capping=None,
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["endDate"], self.expected_none_date_output)
        self.assertEqual(resp_json["data"]["trackingCode"], "")
        self.assertEqual(resp_json["data"]["targeting"]["interest"]["included"], [])
        self.assertEqual(resp_json["data"]["targeting"]["browsers"]["included"], [])
        self.assertEqual(resp_json["data"]["targeting"]["browsers"]["excluded"], [])
        self.assertEqual(resp_json["data"]["dailyBudget"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["autopilot"]["dailyBudget"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["clickCappingDailyAdGroupMaxClicks"], self.expected_none_click_output)
        self.assertEqual(resp_json["data"]["clickCappingDailyClickBudget"], self.expected_none_click_output)
        self.assertEqual(resp_json["data"]["dayparting"], {})
        self.assertEqual(
            resp_json["data"]["targeting"]["geo"]["included"],
            {"countries": [], "regions": [], "dma": [], "cities": [], "postalCodes": []},
        )
        self.assertEqual(resp_json["data"]["frequencyCapping"], self.expected_none_frequency_capping_output)

    def test_adgroups_publisher_groups(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        pg_one = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)
        pg_two = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)

        put_data = self.adgroup_repr(
            id=ad_group.id,
            campaign_id=campaign.id,
            whitelist_publisher_groups=[pg_one.id],
            blacklist_publisher_groups=[pg_two.id],
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, whitelist_publisher_groups=[-1])
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, blacklist_publisher_groups=[-1])
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_custom_audiences(self):
        request = magic_mixer.blend_request_user()
        request.user = self.user

        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        pixel_one = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel one")
        audience_one = core.features.audiences.Audience.objects.create(
            request, "test", pixel_one, 10, 20, [{"type": 2, "value": "test_rule"}]
        )
        pixel_two = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel two")
        audience_two = core.features.audiences.Audience.objects.create(
            request, "test", pixel_two, 10, 20, [{"type": 2, "value": "test_rule"}]
        )

        put_data = self.adgroup_repr(
            id=ad_group.id,
            campaign_id=campaign.id,
            audience_targeting=[audience_one.id],
            exclusion_audience_targeting=[audience_two.id],
        )
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, audience_targeting=[-1])
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, exclusion_audience_targeting=[-1])
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_language_matching(self):
        account = self.mix_account(
            self.user, permissions=[Permission.READ, Permission.WRITE], agency__uses_realtime_autopilot=True
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        settings = ad_group.get_current_settings().copy_settings()
        settings.language_targeting_enabled = False
        settings.save(None)

        self.assertFalse(ad_group.settings.language_targeting_enabled)

        put_data = self.adgroup_repr(id=ad_group.id, campaign_id=campaign.id, language_targeting_enabled=True)
        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"]["targeting"]["language"]["matchingEnabled"], True)
        self.validate_against_db(resp_json["data"])

    def test_put_adgroups_invalid_target_connection_types(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        put_data = resp_json["data"].copy()
        put_data["name"] = "Demo adgroup"

        put_data["targeting"]["connectionTypes"] = ["abcd"]

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_put_adgroups_valid_target_connection_types(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        put_data = resp_json["data"].copy()
        put_data["name"] = "Demo adgroup"

        put_data["targeting"]["connectionTypes"] = [
            dash.constants.ConnectionType.get_name(dash.constants.ConnectionType.WIFI)
        ]

        r = self.client.put(
            reverse("restapi.adgroup.v1:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(
            [dash.constants.ConnectionType.get_name(dash.constants.ConnectionType.WIFI)],
            resp_json["data"]["targeting"]["connectionTypes"],
        )

    def test_put_adgroups_invalid_target_browsers(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        put_data = resp_json["data"].copy()
        put_data["name"] = "Demo adgroup"

        put_data["targeting"]["browsers"] = {
            "included": [{"family": dash.constants.BrowserFamily.CHROME}],
            "excluded": [{"family": dash.constants.BrowserFamily.EDGE}],
        }

        r = self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_put_adgroups_invalid_target_browser_device_type(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        put_data = resp_json["data"].copy()
        put_data["name"] = "Demo adgroup"

        put_data["targeting"]["devices"] = [dash.constants.AdTargetDevice.MOBILE]
        put_data["targeting"]["browsers"] = {"included": [{"family": dash.constants.BrowserFamily.IE}], "excluded": []}

        r = self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_put_adgroups_valid_target_browsers(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        put_data = resp_json["data"].copy()
        put_data["name"] = "Demo adgroup"

        put_data["targeting"]["browsers"] = {
            "included": [{"family": dash.constants.BrowserFamily.CHROME}],
            "excluded": [],
        }

        r = self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(
            {"family": dash.constants.BrowserFamily.CHROME}, resp_json["data"]["targeting"]["browsers"]["included"][0]
        )

        put_data["targeting"]["browsers"] = {
            "included": [],
            "excluded": [{"family": dash.constants.BrowserFamily.EDGE}],
        }

        r = self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(
            {"family": dash.constants.BrowserFamily.EDGE}, resp_json["data"]["targeting"]["browsers"]["excluded"][0]
        )

    def test_put_adgroups_valid_browsers_oen(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        put_data = resp_json["data"].copy()
        put_data["name"] = "Demo adgroup"

        put_data["targeting"]["browsersOen"] = [{"family": dash.constants.BrowserFamily.CHROME}]

        r = self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertEqual(
            {"family": dash.constants.BrowserFamily.CHROME}, resp_json["data"]["targeting"]["browsersOen"][0]
        )

    def test_put_adgroups_invalid_browsers_oen(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        put_data = resp_json["data"].copy()
        put_data["name"] = "Demo adgroup"

        put_data["targeting"]["browsersOen"] = [{"family": "abc"}]

        r = self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_put_adgroups_browsers_and_browsers_oen_together(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)
        put_data = resp_json["data"].copy()
        put_data["name"] = "Demo adgroup"

        # setting "browsersOen" field together with "browsers" should not override "browsers" field
        put_data["targeting"]["browsers"] = {
            "included": [{"family": dash.constants.BrowserFamily.CHROME}],
            "excluded": [],
        }
        put_data["targeting"]["browsersOen"] = [{"family": dash.constants.BrowserFamily.CHROME}]

        r = self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertEqual(
            {"family": dash.constants.BrowserFamily.CHROME}, resp_json["data"]["targeting"]["browsers"]["included"][0]
        )
        self.assertEqual([], resp_json["data"]["targeting"]["browsers"]["excluded"])

        put_data["targeting"]["browsers"] = {
            "included": [],
            "excluded": [{"family": dash.constants.BrowserFamily.CHROME}],
        }
        put_data["targeting"]["browsersOen"] = [{"family": dash.constants.BrowserFamily.CHROME}]

        r = self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        self.assertEqual(
            {"family": dash.constants.BrowserFamily.CHROME}, resp_json["data"]["targeting"]["browsers"]["excluded"][0]
        )
        self.assertEqual([], resp_json["data"]["targeting"]["browsers"]["included"])
