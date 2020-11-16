import datetime
import json
from decimal import Decimal

from django.urls import reverse
from mock import patch

import core.features.bcm
import dash.constants
import dash.features.ga
import dash.features.geolocation
import dash.models
from core.features import bid_modifiers
from utils import dates_helper
from utils import zlogging
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest

logger = zlogging.getLogger(__name__)
logger.setLevel(zlogging.INFO)


class AdGroupsTest(K1APIBaseTest):
    @patch("utils.dates_helper.local_today", return_value=datetime.date(2014, 1, 1))
    def test_get_ad_groups_with_id(self, mock_local_today):
        start_date = datetime.date(2014, 1, 1)
        end_date = datetime.date(2015, 1, 1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=ad_group.campaign.account,
            start_date=start_date,
            end_date=end_date,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500,
            service_fee=Decimal("0.20"),
            license_fee=Decimal("0.10"),
        )
        request = magic_mixer.blend_request_user()
        core.features.bcm.BudgetLineItem.objects.create(
            request, ad_group.campaign, credit, start_date, end_date, 100, Decimal("0.1"), "test"
        )

        response = self.client.get(reverse("k1api.ad_groups"), {"ad_group_ids": 1})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 1)

        self.assertDictEqual(
            data[0],
            {
                "id": 1,
                "name": "test adgroup 1",
                "external_name": "ONE: test account 1 / test campaign 1 / test adgroup 1 / 1",
                "start_date": "2014-06-04",
                "end_date": None,
                "time_zone": "America/New_York",
                "bidding_type": dash.constants.BiddingType.CPC,
                "bid": "0.4536",
                "autopilot_state": dash.constants.B1AutopilotState.INACTIVE,
                "brand_name": "brand1",
                "display_url": "brand1.com",
                "tracking_codes": "tracking1&tracking2",
                "enable_ga_tracking": True,
                "enable_adobe_tracking": False,
                "adobe_tracking_param": "",
                "target_devices": [],
                "target_os": None,
                "target_browsers": None,
                "exclusion_target_browsers": None,
                "target_connection_types": None,
                "target_placements": None,  # TODO: plac: remove after k1 merge
                "target_environments": None,
                "iab_category": "IAB24",
                "campaign_language": "en",
                "target_regions": [],
                "exclusion_target_regions": [],
                "retargeting": [
                    {"event_id": "100", "event_type": "redirect_adgroup", "exclusion": False},
                    {"event_id": "200", "event_type": "redirect_adgroup", "exclusion": True},
                    {"event_id": "1", "event_type": "aud", "exclusion": False},
                    {"event_id": "2", "event_type": "aud", "exclusion": True},
                ],
                "demographic_targeting": ["or", "bluekai:1", "bluekai:2"],
                "interest_targeting": ["tech", "entertainment"],
                "exclusion_interest_targeting": ["politics", "war"],
                "language_targeting_enabled": False,
                "campaign_id": 1,
                "campaign_name": "test campaign 1",
                "campaign_type": dash.constants.CampaignType.CONTENT,
                "account_id": 1,
                "account_name": "test account 1",
                "agency_id": 20,
                "agency_name": "test agency 1",
                "goal_types": [2, 5],
                "goals": [
                    {"campaign_id": 1, "conversion_goal": None, "id": 2, "primary": True, "type": 2, "values": []},
                    {"campaign_id": 1, "conversion_goal": None, "id": 1, "primary": False, "type": 5, "values": []},
                ],
                "b1_sources_group": {"daily_budget": "6.4800000000000000", "enabled": True, "state": 2},
                "dayparting": {"monday": [1, 2, 3], "timezone": "CET"},
                "whitelist_publisher_groups": [1, 2, 5, 6, 9, 10],
                "blacklist_publisher_groups": [3, 4, 7, 8, 11, 12],
                "delivery_type": 1,
                "click_capping_daily_ad_group_max_clicks": 15,
                "click_capping_daily_click_budget": "5.0000",
                "custom_flags": {"flag_1": True, "flag_2": True, "flag_3": True, "flag_4": True},
                "amplify_review": True,
                "freqcap_account": 40,
                "freqcap_campaign": 30,
                "freqcap_adgroup": 20,
                "additional_data": {
                    "ob_campaign_id": 1000000305,
                    "ob_marketer_id": 33424,
                    "min_cpc": "0.030000",
                    "max_cpc": "10.000000",
                    "kpio": {
                        "max_factor": "2.000",
                        "enabled": True,
                        "experiment_enabled": True,
                        "control_group_percentage": "0.200",
                    },
                    "high_impact": False,
                },
            },
        )

    def test_get_ad_groups_with_id_with_some_flags(self):
        a = dash.models.AdGroup.objects.get(pk=1)
        a.bidding_type = dash.constants.BiddingType.CPM
        a.custom_flags = {}
        a.save(None)
        a.campaign.custom_flags = {}
        a.campaign.save()

        response = self.client.get(reverse("k1api.ad_groups"), {"ad_group_ids": 1})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 1)

        self.assertDictEqual(
            data[0],
            {
                "id": 1,
                "name": "test adgroup 1",
                "external_name": "ONE: test account 1 / test campaign 1 / test adgroup 1 / 1",
                "start_date": "2014-06-04",
                "end_date": None,
                "time_zone": "America/New_York",
                "bidding_type": dash.constants.BiddingType.CPM,
                "bid": "1.7000",
                "autopilot_state": dash.constants.B1AutopilotState.INACTIVE,
                "brand_name": "brand1",
                "display_url": "brand1.com",
                "tracking_codes": "tracking1&tracking2",
                "enable_ga_tracking": True,
                "enable_adobe_tracking": False,
                "adobe_tracking_param": "",
                "target_devices": [],
                "target_os": None,
                "target_browsers": None,
                "exclusion_target_browsers": None,
                "target_connection_types": None,
                "target_placements": None,  # TODO: plac: remove after k1 merge
                "target_environments": None,
                "iab_category": "IAB24",
                "campaign_language": "en",
                "target_regions": [],
                "exclusion_target_regions": [],
                "retargeting": [
                    {"event_id": "100", "event_type": "redirect_adgroup", "exclusion": False},
                    {"event_id": "200", "event_type": "redirect_adgroup", "exclusion": True},
                    {"event_id": "1", "event_type": "aud", "exclusion": False},
                    {"event_id": "2", "event_type": "aud", "exclusion": True},
                ],
                "demographic_targeting": ["or", "bluekai:1", "bluekai:2"],
                "interest_targeting": ["tech", "entertainment"],
                "exclusion_interest_targeting": ["politics", "war"],
                "language_targeting_enabled": False,
                "campaign_id": 1,
                "campaign_name": "test campaign 1",
                "campaign_type": dash.constants.CampaignType.CONTENT,
                "account_id": 1,
                "account_name": "test account 1",
                "agency_id": 20,
                "agency_name": "test agency 1",
                "goal_types": [2, 5],
                "goals": [
                    {"campaign_id": 1, "conversion_goal": None, "id": 2, "primary": True, "type": 2, "values": []},
                    {"campaign_id": 1, "conversion_goal": None, "id": 1, "primary": False, "type": 5, "values": []},
                ],
                "b1_sources_group": {"daily_budget": "10.0000000000000000", "enabled": True, "state": 2},
                "dayparting": {"monday": [1, 2, 3], "timezone": "CET"},
                "whitelist_publisher_groups": [1, 2, 5, 6, 9, 10],
                "blacklist_publisher_groups": [3, 4, 7, 8, 11, 12],
                "delivery_type": 1,
                "click_capping_daily_ad_group_max_clicks": 15,
                "click_capping_daily_click_budget": "5.0000",
                "custom_flags": {"flag_1": False, "flag_2": True, "flag_3": True, "flag_4": True},
                "amplify_review": True,
                "freqcap_account": 40,
                "freqcap_campaign": 30,
                "freqcap_adgroup": 20,
                "additional_data": {
                    "ob_campaign_id": 1000000305,
                    "ob_marketer_id": 33424,
                    "min_cpc": "0.030000",
                    "max_cpc": "10.000000",
                    "kpio": {
                        "max_factor": "2.000",
                        "enabled": True,
                        "experiment_enabled": True,
                        "control_group_percentage": "0.200",
                    },
                    "high_impact": False,
                },
            },
        )

    def test_get_ad_groups_autopilot_state(self):
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account__agency__uses_realtime_autopilot=True)

        # ad group cpc+budget autopilot on
        self.assertEqual(
            dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET, ad_group.settings.autopilot_state
        )
        response = self.client.get(reverse("k1api.ad_groups"), {"ad_group_ids": ad_group.id})
        data = json.loads(response.content)["response"][0]
        self.assertEqual(dash.constants.B1AutopilotState.ACTIVE, data["autopilot_state"])

        # ad group cpc autopilot on
        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC)
        response = self.client.get(reverse("k1api.ad_groups"), {"ad_group_ids": ad_group.id})
        data = json.loads(response.content)["response"][0]
        self.assertEqual(dash.constants.B1AutopilotState.ACTIVE, data["autopilot_state"])

        # ad group autopilot off
        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
        response = self.client.get(reverse("k1api.ad_groups"), {"ad_group_ids": ad_group.id})
        data = json.loads(response.content)["response"][0]
        self.assertEqual(dash.constants.B1AutopilotState.INACTIVE, data["autopilot_state"])

    # TODO: RTAP: LEGACY
    def test_get_ad_groups_autopilot_state_legacy(self):
        ad_group = magic_mixer.blend(dash.models.AdGroup)

        # ad group cpc+budget autopilot on
        self.assertEqual(
            dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET, ad_group.settings.autopilot_state
        )
        response = self.client.get(reverse("k1api.ad_groups"), {"ad_group_ids": ad_group.id})
        data = json.loads(response.content)["response"][0]
        self.assertEqual(dash.constants.B1AutopilotState.INACTIVE, data["autopilot_state"])

        # ad group cpc autopilot on
        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC)
        response = self.client.get(reverse("k1api.ad_groups"), {"ad_group_ids": ad_group.id})
        data = json.loads(response.content)["response"][0]
        self.assertEqual(dash.constants.B1AutopilotState.INACTIVE, data["autopilot_state"])

        # ad group autopilot off
        ad_group.settings.update_unsafe(None, autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
        response = self.client.get(reverse("k1api.ad_groups"), {"ad_group_ids": ad_group.id})
        data = json.loads(response.content)["response"][0]
        self.assertEqual(dash.constants.B1AutopilotState.INACTIVE, data["autopilot_state"])

    @patch("utils.redirector_helper.insert_adgroup")
    def test_get_ad_groups(self, mock_redirector):
        n = 10
        source = magic_mixer.blend(dash.models.Source, source_type__type="abc")
        ad_groups = magic_mixer.cycle(n).blend(dash.models.AdGroup, campaign_id=1)
        magic_mixer.cycle(n).blend(dash.models.AdGroupSource, ad_group=(ag for ag in ad_groups), source=source)
        for ad_group in ad_groups:
            for ad_group_source in ad_group.adgroupsource_set.all():
                magic_mixer.blend(
                    bid_modifiers.BidModifier,
                    ad_group=ad_group,
                    type=bid_modifiers.BidModifierType.SOURCE,
                    target=str(ad_group_source.source.id),
                    modifier=1.0,
                )
        for ad_group in ad_groups:
            ad_group.settings.update_unsafe(None, brand_name="old")
        for ad_group in ad_groups:
            ad_group.settings.update_unsafe(None, brand_name="new")

        # make the first one archived
        request = magic_mixer.blend_request_user()
        ad_groups[0].settings.update(request, archived=True)

        response = self.client.get(reverse("k1api.ad_groups"), {"source_types": "abc"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(
            [{"id": obj["id"], "brand_name": obj["brand_name"]} for obj in data],
            [{"id": obj.id, "brand_name": obj.settings.brand_name} for obj in ad_groups[1:]],
        )

    @patch("automation.campaignstop.get_campaignstop_states")
    def test_get_ad_groups_campaignstop_start_date(self, mock_get_campaignstop_states):
        mock_get_campaignstop_states.return_value = {}
        source = magic_mixer.blend(dash.models.Source, source_type__type="abc")
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign_id=1)
        ad_group.settings.update(None, start_date=None)
        ad_group_source = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source=source)
        magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            target=str(ad_group_source.source.id),
            modifier=1.0,
        )

        response = self.client.get(reverse("k1api.ad_groups"), {"source_types": "abc"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(data[0]["start_date"], None)

        ad_group.settings.update(None, start_date=dates_helper.local_today())

        response = self.client.get(reverse("k1api.ad_groups"), {"source_types": "abc"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(data[0]["start_date"], dates_helper.local_today().isoformat())

        min_allowed_start_date = dates_helper.days_after(dates_helper.local_today(), 10)
        mock_get_campaignstop_states.return_value = {
            ad_group.campaign_id: {"min_allowed_start_date": min_allowed_start_date}
        }

        response = self.client.get(reverse("k1api.ad_groups"), {"source_types": "abc"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(data[0]["start_date"], min_allowed_start_date.isoformat())

    @patch("automation.campaignstop.get_campaignstop_states")
    def test_get_ad_groups_campaignstop_end_date(self, mock_get_campaignstop_states):
        mock_get_campaignstop_states.return_value = {}
        source = magic_mixer.blend(dash.models.Source, source_type__type="abc")
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign_id=1)
        ad_group.settings.update(None, end_date=None)
        ad_group_source = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source=source)
        magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            target=str(ad_group_source.source.id),
            modifier=1.0,
        )

        response = self.client.get(reverse("k1api.ad_groups"), {"source_types": "abc"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(data[0]["end_date"], None)

        end_date = dates_helper.days_after(dates_helper.local_today(), 10)
        ad_group.settings.update(None, end_date=end_date)

        response = self.client.get(reverse("k1api.ad_groups"), {"source_types": "abc"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(data[0]["end_date"], end_date.isoformat())

        mock_get_campaignstop_states.return_value = {
            ad_group.campaign_id: {"max_allowed_end_date": dates_helper.local_today()}
        }

        response = self.client.get(reverse("k1api.ad_groups"), {"source_types": "abc"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(data[0]["end_date"], dates_helper.local_today().isoformat())

    def test_get_ad_groups_pagination(self):
        n = 10
        source = magic_mixer.blend(dash.models.Source, source_type__type="abc")
        ad_groups = magic_mixer.cycle(n).blend(dash.models.AdGroup, campaign_id=1)
        magic_mixer.cycle(n).blend(dash.models.AdGroupSource, ad_group=(ag for ag in ad_groups), source=source)
        response = self.client.get(
            reverse("k1api.ad_groups"), {"source_types": "abc", "marker": ad_groups[2].id, "limit": 5}
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual([obj["id"] for obj in data], [obj.id for obj in ad_groups[3:8]])

    def test_get_ad_groups_exclude_display(self):
        campaign_native = magic_mixer.blend(dash.models.Campaign, type=dash.constants.CampaignType.CONTENT)
        campaign_display = magic_mixer.blend(dash.models.Campaign, type=dash.constants.CampaignType.DISPLAY)

        ad_groups_native = magic_mixer.cycle(10).blend(dash.models.AdGroup, campaign=campaign_native)
        ad_groups_display = magic_mixer.cycle(10).blend(dash.models.AdGroup, campaign=campaign_display)

        response = self.client.get(
            reverse("k1api.ad_groups"),
            {
                "ad_group_ids": ",".join(str(ag.id) for ag in list(set(ad_groups_native) | set(ad_groups_display))),
                "exclude_display": "true",
            },
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]
        self.assertEqual(set([obj["id"] for obj in data]), set([obj.id for obj in ad_groups_native]))
