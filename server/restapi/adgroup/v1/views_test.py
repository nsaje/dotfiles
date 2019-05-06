import datetime
import json
import string
from decimal import Decimal

import mock
from django.urls import reverse

import dash.models
import restapi.serializers
import utils.test_helper
from automation import autopilot
from dash import constants
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class AdGroupViewSetTest(RESTAPITest):

    expected_none_date_output = None
    expected_none_decimal_output = ""
    expected_none_click_output = None
    expected_none_frequency_capping_output = None

    def adgroup_repr(
        cls,
        id=1,
        campaign_id=1,
        name="My test ad group",
        bidding_type=constants.BiddingType.CPC,
        state=constants.AdGroupSettingsState.INACTIVE,
        archived=False,
        start_date=datetime.date.today(),
        end_date=None,
        max_cpc="0.600",
        max_cpm=None,
        daily_budget="15.00",
        tracking_code="a=b",
        target_regions={"countries": ["US"], "postalCodes": ["CA:12345"]},
        exclusion_target_regions={},
        target_devices=[constants.AdTargetDevice.DESKTOP],
        target_placements=[constants.Placement.APP],
        target_os=[{"name": constants.OperatingSystem.ANDROID}],
        target_browsers=[{"family": constants.BrowserFamily.CHROME}],
        interest_targeting=["women", "fashion"],
        exclusion_interest_targeting=["politics"],
        demographic_targeting=["and", "bluekai:671901", ["or", "lotame:123", "outbrain:123"]],
        autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        autopilot_daily_budget="50.00",
        dayparting={},
        whitelist_publisher_groups=[153],
        blacklist_publisher_groups=[154],
        audience_targeting=[123],
        exclusion_audience_targeting=[124],
        retargeting_ad_groups=[2050],
        exclusion_retargeting_ad_groups=[2051],
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
            "id": str(id),
            "campaignId": str(campaign_id),
            "name": name,
            "biddingType": constants.BiddingType.get_name(bidding_type),
            "state": constants.AdGroupSettingsState.get_name(state),
            "archived": archived,
            "startDate": start_date,
            "endDate": end_date if end_date else cls.expected_none_date_output,
            "maxCpc": Decimal(max_cpc).quantize(Decimal("1.000"))
            if max_cpc and max_cpm is None
            else cls.expected_none_decimal_output,
            "maxCpm": Decimal(max_cpm).quantize(Decimal("1.000")) if max_cpm else cls.expected_none_decimal_output,
            "dailyBudget": Decimal(daily_budget).quantize(Decimal("1.00"))
            if daily_budget
            else cls.expected_none_decimal_output,
            "trackingCode": tracking_code,
            "targeting": {
                "geo": {"included": final_target_regions, "excluded": final_exclusion_target_regions},
                "devices": restapi.serializers.targeting.DevicesSerializer(target_devices).data,
                "placements": restapi.serializers.targeting.PlacementsSerializer(target_placements).data,
                "os": restapi.serializers.targeting.OSsSerializer(target_os).data,
                "browsers": restapi.serializers.targeting.BrowsersSerializer(target_browsers).data,
                "interest": {
                    "included": [constants.InterestCategory.get_name(i) for i in interest_targeting],
                    "excluded": [constants.InterestCategory.get_name(i) for i in exclusion_interest_targeting],
                },
                "audience": restapi.serializers.targeting.AudienceSerializer(demographic_targeting).data,
                "publisherGroups": {"included": whitelist_publisher_groups, "excluded": blacklist_publisher_groups},
                "customAudiences": {"included": audience_targeting, "excluded": exclusion_audience_targeting},
                "retargetingAdGroups": {"included": retargeting_ad_groups, "excluded": exclusion_retargeting_ad_groups},
                "language": {"matchingEnabled": language_targeting_enabled},
            },
            "autopilot": {
                "state": constants.AdGroupSettingsAutopilotState.get_name(autopilot_state),
                "dailyBudget": Decimal(autopilot_daily_budget).quantize(Decimal("1.00"))
                if autopilot_daily_budget
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
            state=settings_db.state,
            archived=settings_db.archived,
            start_date=settings_db.start_date,
            end_date=settings_db.end_date,
            max_cpc=None if adgroup_db.bidding_type == constants.BiddingType.CPM else settings_db.local_cpc_cc,
            max_cpm=settings_db.local_max_cpm if adgroup_db.bidding_type == constants.BiddingType.CPM else None,
            daily_budget=settings_db.daily_budget_cc,
            tracking_code=settings_db.tracking_code,
            target_regions=self._partition_regions(settings_db.target_regions),
            interest_targeting=settings_db.interest_targeting,
            exclusion_interest_targeting=settings_db.exclusion_interest_targeting,
            demographic_targeting=settings_db.bluekai_targeting,
            language_targeting_enabled=settings_db.language_targeting_enabled,
            autopilot_state=settings_db.autopilot_state,
            autopilot_daily_budget=settings_db.local_autopilot_daily_budget,
            dayparting=settings_db.dayparting,
            whitelist_publisher_groups=settings_db.whitelist_publisher_groups,
            blacklist_publisher_groups=settings_db.blacklist_publisher_groups,
            audience_targeting=settings_db.audience_targeting,
            exclusion_audience_targeting=settings_db.exclusion_audience_targeting,
            retargeting_ad_groups=settings_db.retargeting_ad_groups,
            exclusion_retargeting_ad_groups=settings_db.exclusion_retargeting_ad_groups,
            target_devices=settings_db.target_devices,
            target_placements=settings_db.target_placements,
            target_os=settings_db.target_os,
            target_browsers=settings_db.target_browsers,
            click_capping_daily_ad_group_max_clicks=settings_db.click_capping_daily_ad_group_max_clicks,
            click_capping_daily_click_budget=settings_db.click_capping_daily_click_budget,
            frequency_capping=settings_db.frequency_capping,
        )
        self.assertEqual(expected, adgroup)

    def test_adgroups_get_cpc(self):
        r = self.client.get(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertTrue(resp_json["data"]["maxCpc"])
        self.assertFalse(resp_json["data"]["maxCpm"])

    def test_adgroups_get_cpm(self):
        ad_group = dash.models.AdGroup.objects.get(id=2040)
        ad_group.bidding_type = constants.BiddingType.CPM
        ad_group.save(None)
        r = self.client.get(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertFalse(resp_json["data"]["maxCpc"])
        self.assertTrue(resp_json["data"]["maxCpm"])

    def test_adgroups_list(self):
        r = self.client.get(reverse("v1:adgroups_list"))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_adgroups_list_campaign_id(self):
        campaign_id = 608
        r = self.client.get(reverse("v1:adgroups_list"), data={"campaignId": campaign_id})
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)
            self.assertEqual(int(item["campaignId"]), campaign_id)

    def test_adgroups_list_campaign_id_invalid(self):
        r = self.client.get(reverse("v1:adgroups_list"), data={"campaignId": 1000})
        self.assertResponseError(r, "MissingDataError")

    def test_adgroups_list_pagination(self):
        campaign = magic_mixer.blend(dash.models.Campaign, account__users=[self.user])
        magic_mixer.cycle(10).blend(dash.models.AdGroup, campaign=campaign)
        r = self.client.get(reverse("v1:adgroups_list"), {"campaignId": campaign.id})
        r_paginated = self.client.get(reverse("v1:adgroups_list"), {"campaignId": campaign.id, "limit": 2, "offset": 5})
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json["data"][5:7], resp_json_paginated["data"])

    # def test_adgroups_list_exclude_archived(self):  # TODO: ARCHIVING
    #     campaign = magic_mixer.blend(dash.models.Campaign, account__users=[self.user])
    #     magic_mixer.cycle(3).blend(dash.models.AdGroup, campaign=campaign, archived=False)
    #     magic_mixer.cycle(2).blend(dash.models.AdGroup, campaign=campaign, archived=True)
    #     r = self.client.get(reverse("v1:adgroups_list"), {"campaignId": campaign.id})
    #     resp_json = self.assertResponseValid(r, data_type=list)
    #     self.assertEqual(3, len(resp_json["data"]))
    #     for item in resp_json["data"]:
    #         self.validate_against_db(item)
    #         self.assertFalse(item["archived"])

    # def test_adgroups_list_include_archived(self):  # TODO: ARCHIVING
    #     campaign = magic_mixer.blend(dash.models.Campaign, account__users=[self.user])
    #     magic_mixer.cycle(3).blend(dash.models.AdGroup, campaign=campaign, archived=False)
    #     magic_mixer.cycle(2).blend(dash.models.AdGroup, campaign=campaign, archived=True)
    #     r = self.client.get(reverse("v1:adgroups_list"), {"campaignId": campaign.id, "includeArchived": 1})
    #     resp_json = self.assertResponseValid(r, data_type=list)
    #     self.assertEqual(5, len(resp_json["data"]))
    #     for item in resp_json["data"]:
    #         self.validate_against_db(item)

    def test_adgroups_list_campaign_filter(self):
        # TODO(nsaje): create a prettier test, this one is urgent and hackish
        account1 = magic_mixer.blend(dash.models.Account, users=[self.user])
        adgroup1_account1 = magic_mixer.blend(dash.models.AdGroup, campaign__account=account1)
        adgroup1_account1.get_current_settings().copy_settings().save(None)
        adgroup2_account1 = magic_mixer.blend(dash.models.AdGroup, campaign__account=account1)
        adgroup2_account1.get_current_settings().copy_settings().save(None)
        account2 = magic_mixer.blend(dash.models.Account)
        adgroup1_account2 = magic_mixer.blend(dash.models.AdGroup, campaign__account=account2)
        adgroup1_account2.get_current_settings().copy_settings().save(None)

        r = self.client.get(reverse("v1:adgroups_list"), {"campaignId": adgroup1_account1.campaign_id})
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)
        self.assertEqual(len(resp_json["data"]), 1)
        self.assertEqual(resp_json["data"][0]["id"], str(adgroup1_account1.id))

    def test_adgroups_post_cpc(self):
        new_ad_group = self.adgroup_repr(campaign_id=608, name="Test Group")
        del new_ad_group["id"]
        r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_ad_group["id"] = resp_json["data"]["id"]
        self.assertEqual(resp_json["data"], new_ad_group)
        adgroup_db = dash.models.AdGroup.objects.get(pk=new_ad_group["id"])
        self.assertEqual(adgroup_db.name, adgroup_db.get_current_settings().ad_group_name)
        self.assertTrue(resp_json["data"]["maxCpc"])
        self.assertFalse(resp_json["data"]["maxCpm"])

    def test_adgroups_post_cpm(self):
        new_ad_group = self.adgroup_repr(
            campaign_id=608, name="Test Group", bidding_type=constants.BiddingType.CPM, max_cpm="3.100"
        )
        del new_ad_group["id"]
        r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_ad_group["id"] = resp_json["data"]["id"]
        self.assertEqual(resp_json["data"], new_ad_group)
        self.assertFalse(resp_json["data"]["maxCpc"])
        self.assertTrue(resp_json["data"]["maxCpm"])

    # def test_adgroups_post_campaign_archived(self):  # TODO: ARCHIVING
    #     account = magic_mixer.blend(dash.models.Account, users=[self.user])
    #     campaign = magic_mixer.blend(dash.models.Campaign, account=account, archived=True)
    #     new_ad_group = self.adgroup_repr(campaign_id=campaign.id, name="Test Group")
    #     del new_ad_group["id"]
    #     r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
    #     self.assertResponseError(r, "ValidationError")
    #     self.assertEqual(
    #         ["Can not create an ad group on an archived campaign."], json.loads(r.content)["details"]["campaignId"]
    #     )

    def test_adgroups_post_no_campaign_id(self):
        new_ad_group = self.adgroup_repr(campaign_id=608, name="Test Group")
        del new_ad_group["id"]
        del new_ad_group["campaignId"]
        r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_post_no_state(self):
        new_ad_group = self.adgroup_repr(campaign_id=608, name="Test Group")
        del new_ad_group["id"]
        del new_ad_group["state"]
        r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["state"], "INACTIVE")

    def test_adgroups_post_wrong_campaign_id(self):
        new_ad_group = self.adgroup_repr(campaign_id=1000, name="Test Group")
        del new_ad_group["id"]
        r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "MissingDataError")

    def test_adgroups_post_no_name(self):
        new_ad_group = self.adgroup_repr(campaign_id=608)
        del new_ad_group["id"]
        del new_ad_group["name"]
        r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_cpc(self):
        test_adgroup = self.adgroup_repr(id=2040, campaign_id=608)
        r = self.client.put(
            reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=test_adgroup, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"], test_adgroup)

    def test_adgroups_put_cpm(self):
        ad_group = dash.models.AdGroup.objects.get(id=2040)
        ad_group.bidding_type = constants.BiddingType.CPM
        ad_group.save(None)
        test_adgroup = self.adgroup_repr(
            id=2040, campaign_id=608, bidding_type=constants.BiddingType.CPM, max_cpm="3.100"
        )
        r = self.client.put(
            reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=test_adgroup, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"], test_adgroup)
        self.assertFalse(resp_json["data"]["maxCpc"])
        self.assertTrue(resp_json["data"]["maxCpm"])

    def test_adgroups_put_name(self):
        adgroup = self.adgroup_repr(name="New Name")
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        adgroup_db = dash.models.AdGroup.objects.get(pk=2040)
        self.assertEqual(adgroup_db.name, adgroup_db.get_current_settings().ad_group_name)

    def test_adgroups_put_frequency_capping(self):
        adgroup = self.adgroup_repr(frequency_capping=33)
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["frequencyCapping"], 33)

    def test_adgroups_put_empty(self):
        put_data = {}
        settings_count = dash.models.AdGroupSettings.objects.filter(ad_group_id=2040).count()
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=put_data, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(settings_count, dash.models.CampaignSettings.objects.filter(campaign_id=608).count())

    def test_adgroups_put_state(self):
        adgroup = self.adgroup_repr(state=constants.AdGroupSettingsState.INACTIVE)
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["state"], "INACTIVE")

    def test_adgroups_put_invalid_state(self):
        r = self.client.put(
            reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data={"state": "NOTVALID"}, format="json"
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_archive_restore(self):
        r = self.client.put(
            reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data={"archived": True}, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["archived"], True)

        r = self.client.put(
            reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data={"archived": False}, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["archived"], False)

    @mock.patch.object(autopilot, "recalculate_budgets_ad_group", autospec=True)
    def test_adgroups_put_autopilot_budget(self, mock_autopilot):
        ag = dash.models.AdGroup.objects.get(pk=2040)
        new_settings = ag.get_current_settings().copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.save(None)
        test_adgroup = self.adgroup_repr(
            id=2040,
            campaign_id=608,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            autopilot_daily_budget="20.00",
        )
        r = self.client.put(
            reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=test_adgroup, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"], test_adgroup)

    def test_adgroups_put_invalid_autopilot_state(self):
        ag = dash.models.AdGroup.objects.get(pk=2040)
        new_settings = ag.get_current_settings().copy_settings()
        new_settings.b1_sources_group_enabled = False
        new_settings.save(None)
        test_adgroup = self.adgroup_repr(
            id=2040, campaign_id=608, autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        )
        r = self.client.put(
            reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=test_adgroup, format="json"
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_post_high_cpc(self):
        new_ad_group = self.adgroup_repr(campaign_id=608, name="Test Group", max_cpc=Decimal("9000"))
        del new_ad_group["id"]
        r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_low_cpc(self):
        adgroup = self.adgroup_repr(max_cpc="0.0")
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_post_high_cpm(self):
        new_ad_group = self.adgroup_repr(
            campaign_id=608, name="Test Group", max_cpm=Decimal("9000"), bidding_type=constants.BiddingType.CPM
        )
        del new_ad_group["id"]
        r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
        resp_json = json.loads(r.content)
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("25" in resp_json["details"]["maxCpm"][0])

    def test_adgroups_put_low_cpm(self):
        adgroup = self.adgroup_repr(bidding_type=constants.BiddingType.CPM, max_cpm="0.0")
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        resp_json = json.loads(r.content)
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("0.05" in resp_json["details"]["maxCpm"][0])

    def test_adgroups_put_end_date_before_start_date(self):
        adgroup = self.adgroup_repr(
            start_date=datetime.date.today() + datetime.timedelta(days=10),
            end_date=datetime.date.today() + datetime.timedelta(days=7),
        )
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_end_date_in_the_past(self):
        adgroup = self.adgroup_repr(
            start_date=datetime.date.today() + datetime.timedelta(days=10),
            end_date=datetime.date.today() + datetime.timedelta(days=7),
            state=constants.AdGroupSettingsState.ACTIVE,
        )
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_invalid_tracking_code(self):
        adgroup = self.adgroup_repr(tracking_code="_[]...")
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_post_no_targets(self):
        new_ad_group = self.adgroup_repr(campaign_id=608, name="Test Group", target_devices=[])
        del new_ad_group["id"]
        r = self.client.post(reverse("v1:adgroups_list"), data=new_ad_group, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_invalid_timezone(self):
        adgroup = self.adgroup_repr(dayparting={"timezone": "incorrectzone"})
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_put_invalid_hour(self):
        adgroup = self.adgroup_repr(dayparting={"friday": [0, 1, 25]})
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_invalid_bluekai_targeting(self):
        demographic_targeting = ["and", "bluekai:12f3", ["or", "lotame:123", "outbrain:123"]]
        adgroup = self.adgroup_repr(
            audience_targeting=restapi.serializers.targeting.AudienceSerializer(demographic_targeting).data
        )
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_get_permissioned(self):
        utils.test_helper.remove_permissions(
            self.user,
            permissions=[
                "can_set_click_capping",
                "can_set_click_capping_daily_click_budget",
                "can_set_frequency_capping",
                "can_use_language_targeting",
            ],
        )
        r = self.client.get(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}))
        resp_json = self.assertResponseValid(r)
        self.assertFalse("clickCappingDailyAdGroupMaxClicks" in resp_json["data"])
        self.assertFalse("clickCappingDailyClickBudget" in resp_json["data"])
        self.assertFalse("frequencyCapping" in resp_json["data"])
        self.assertFalse("language" in resp_json["data"]["targeting"])
        resp_json["data"]["clickCappingDailyAdGroupMaxClicks"] = self.expected_none_click_output
        resp_json["data"]["clickCappingDailyClickBudget"] = self.expected_none_click_output
        resp_json["data"]["frequencyCapping"] = self.expected_none_frequency_capping_output
        resp_json["data"]["targeting"]["language"] = {"matchingEnabled": False}
        self.validate_against_db(resp_json["data"])

    def test_adgroups_put_blank_strings(self):
        adgroup = self.adgroup_repr(
            end_date="",
            max_cpc="",
            max_cpm="",
            tracking_code="",
            interest_targeting=[],
            target_browsers=None,
            daily_budget="",
            autopilot_daily_budget="",
            click_capping_daily_ad_group_max_clicks="",
            click_capping_daily_click_budget="",
            dayparting={"timezone": ""},
            frequency_capping="",
        )
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["endDate"], self.expected_none_date_output)
        self.assertEqual(resp_json["data"]["maxCpc"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["maxCpm"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["trackingCode"], "")
        self.assertEqual(resp_json["data"]["targeting"]["interest"]["included"], [])
        self.assertEqual(resp_json["data"]["targeting"]["browsers"], [])
        self.assertEqual(resp_json["data"]["dailyBudget"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["autopilot"]["dailyBudget"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["clickCappingDailyAdGroupMaxClicks"], self.expected_none_click_output)
        self.assertEqual(resp_json["data"]["clickCappingDailyClickBudget"], self.expected_none_click_output)
        self.assertEqual(resp_json["data"]["dayparting"]["timezone"], "")
        self.assertEqual(resp_json["data"]["frequencyCapping"], self.expected_none_frequency_capping_output)

    def test_adgroups_put_blank_bid(self):
        ad_group = dash.models.AdGroup.objects.get(id=2040)
        ad_group.settings.update_unsafe(None, cpc_cc=1.1, max_cpm=3.1)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.1000"), ad_group.settings.cpc_cc)
        self.assertEqual(Decimal("3.1000"), ad_group.settings.max_cpm)

        data = self.adgroup_repr(max_cpc="", max_cpm="")
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=data, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["maxCpm"], self.expected_none_decimal_output)
        ad_group.refresh_from_db()
        self.assertIsNone(ad_group.settings.cpc_cc)
        self.assertEqual(Decimal("3.1000"), ad_group.settings.max_cpm)

        ad_group.settings.update_unsafe(None, cpc_cc=1.1, max_cpm=3.1)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.1000"), ad_group.settings.cpc_cc)
        self.assertEqual(Decimal("3.1000"), ad_group.settings.max_cpm)

        data["biddingType"] = "CPM"
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=data, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["maxCpm"], self.expected_none_decimal_output)
        ad_group.refresh_from_db()
        self.assertEqual(Decimal("1.1000"), ad_group.settings.cpc_cc)
        self.assertIsNone(ad_group.settings.max_cpm)

    def test_adgroups_put_none(self):
        adgroup = self.adgroup_repr(
            end_date=None,
            max_cpc=None,
            max_cpm=None,
            tracking_code=None,
            interest_targeting=[],
            target_browsers=None,
            daily_budget=None,
            autopilot_daily_budget=None,
            click_capping_daily_ad_group_max_clicks=None,
            click_capping_daily_click_budget=None,
            dayparting=None,
            target_regions={},
            frequency_capping=None,
        )
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["endDate"], self.expected_none_date_output)
        self.assertEqual(resp_json["data"]["maxCpc"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["maxCpm"], self.expected_none_decimal_output)
        self.assertEqual(resp_json["data"]["trackingCode"], "")
        self.assertEqual(resp_json["data"]["targeting"]["interest"]["included"], [])
        self.assertEqual(resp_json["data"]["targeting"]["browsers"], [])
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
        adgroup = self.adgroup_repr(whitelist_publisher_groups=[153], blacklist_publisher_groups=[154])
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        adgroup = self.adgroup_repr(whitelist_publisher_groups=[1])
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

        adgroup = self.adgroup_repr(blacklist_publisher_groups=[2])
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_custom_audiences(self):
        adgroup = self.adgroup_repr(audience_targeting=[123], exclusion_audience_targeting=[124])
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        adgroup = self.adgroup_repr(audience_targeting=[1])
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")

        adgroup = self.adgroup_repr(exclusion_audience_targeting=[2])
        r = self.client.put(reverse("v1:adgroups_details", kwargs={"ad_group_id": 2040}), data=adgroup, format="json")
        self.assertResponseError(r, "ValidationError")
