import mock
from django.urls import reverse

import core.features.deals
import core.models
import dash.constants
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class AdGroupViewSetTest(RESTAPITest):
    def test_validate_empty(self):
        r = self.client.post(reverse("restapi.adgroup.internal:adgroups_validate"))
        self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        data = {"name": "My ad group 1", "campaignId": "123"}
        r = self.client.post(reverse("restapi.adgroup.internal:adgroups_validate"), data=data, format="json")
        self.assertResponseValid(r, data_type=type(None))

    def test_validate_error(self):
        data = {"name": None, "campaignId": None}
        r = self.client.post(reverse("restapi.adgroup.internal:adgroups_validate"), data=data, format="json")
        r = self.assertResponseError(r, "ValidationError")
        self.assertIn("This field may not be null.", r["details"]["name"][0])
        self.assertIn("This field may not be null.", r["details"]["campaignId"][0])

    @mock.patch("restapi.adgroup.internal.helpers.get_extra_data")
    def test_get_default(self, mock_get_extra_data):
        mock_get_extra_data.return_value = {
            "action_is_waiting": False,
            "can_archive": False,
            "can_restore": False,
            "is_campaign_autopilot_enabled": False,
            "account_id": 12345,
            "currency": dash.constants.Currency.USD,
            "optimization_objective": None,
            "default_settings": {
                "target_regions": [],
                "exclusion_target_regions": [],
                "target_devices": [],
                "target_os": [],
                "target_placements": [],
            },
            "retargetable_ad_groups": [],
            "audiences": [],
            "warnings": {"retargeting": {"sources": []}},
            "hacks": [],
            "deals": [],
        }

        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        r = self.client.get(reverse("restapi.adgroup.internal:adgroups_defaults"), {"campaignId": campaign.id})
        resp_json = self.assertResponseValid(r)

        self.assertIsNone(resp_json["data"]["id"])
        self.assertEqual(resp_json["data"]["name"], "")
        self.assertIsNone(resp_json["data"].get("dailyBudget"))
        self.assertEqual(resp_json["data"]["notes"], "")
        self.assertEqual(resp_json["data"]["redirectPixelUrls"], [])
        self.assertEqual(resp_json["data"]["redirectJavascript"], "")
        self.assertEqual(resp_json["data"]["deals"], [])
        self.assertEqual(
            resp_json["extra"],
            {
                "actionIsWaiting": False,
                "canArchive": False,
                "canRestore": False,
                "isCampaignAutopilotEnabled": False,
                "accountId": "12345",
                "currency": dash.constants.Currency.get_name(dash.constants.Currency.USD),
                "optimizationObjective": "",
                "defaultSettings": {
                    "targetRegions": {"countries": [], "regions": [], "dma": [], "cities": [], "postalCodes": []},
                    "exclusionTargetRegions": {
                        "countries": [],
                        "regions": [],
                        "dma": [],
                        "cities": [],
                        "postalCodes": [],
                    },
                    "targetDevices": [],
                    "targetOs": [],
                    "targetPlacements": [],
                },
                "retargetableAdGroups": [],
                "audiences": [],
                "warnings": {"retargeting": {"sources": []}},
                "hacks": [],
                "deals": [],
            },
        )

    @mock.patch("restapi.adgroup.internal.helpers.get_extra_data")
    def test_get(self, mock_get_extra_data):
        mock_get_extra_data.return_value = {
            "action_is_waiting": False,
            "can_archive": False,
            "can_restore": False,
            "is_campaign_autopilot_enabled": False,
            "account_id": 12345,
            "currency": dash.constants.Currency.USD,
            "optimization_objective": dash.constants.CampaignGoalKPI.CPC,
            "default_settings": {
                "target_regions": [],
                "exclusion_target_regions": [],
                "target_devices": [],
                "target_os": [],
                "target_placements": [],
            },
            "retargetable_ad_groups": [],
            "audiences": [],
            "warnings": {"retargeting": {"sources": []}},
            "hacks": [],
            "deals": [],
        }

        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        settings = ad_group.get_current_settings().copy_settings()
        settings.notes = "adgroups notes"
        settings.redirect_pixel_urls = ["http://a.com/b.jpg", "http://a.com/c.jpg"]
        settings.redirect_javascript = "alert('a')"
        settings.save(None)

        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, adgroup=ad_group)

        r = self.client.get(reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)

        self.assertIsNone(resp_json["data"].get("dailyBudget"))
        self.assertEqual(resp_json["data"]["notes"], settings.notes)
        self.assertEqual(resp_json["data"]["redirectPixelUrls"], settings.redirect_pixel_urls)
        self.assertEqual(resp_json["data"]["redirectJavascript"], settings.redirect_javascript)
        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 1)
        self.assertEqual(
            resp_json["extra"],
            {
                "actionIsWaiting": False,
                "canArchive": False,
                "canRestore": False,
                "isCampaignAutopilotEnabled": False,
                "accountId": "12345",
                "currency": dash.constants.Currency.get_name(dash.constants.Currency.USD),
                "optimizationObjective": dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.CPC),
                "defaultSettings": {
                    "targetRegions": {"countries": [], "regions": [], "dma": [], "cities": [], "postalCodes": []},
                    "exclusionTargetRegions": {
                        "countries": [],
                        "regions": [],
                        "dma": [],
                        "cities": [],
                        "postalCodes": [],
                    },
                    "targetDevices": [],
                    "targetOs": [],
                    "targetPlacements": [],
                },
                "retargetableAdGroups": [],
                "audiences": [],
                "warnings": {"retargeting": {"sources": []}},
                "hacks": [],
                "deals": [],
            },
        )

    @mock.patch.object(core.models.settings.AdGroupSettings, "update")
    def test_ad_group_state_set_to_inactive_on_b1_sources_group_enabled_update(self, mock_ad_group_settings_update):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        settings = ad_group.get_current_settings().copy_settings()
        settings.b1_sources_group_enabled = False
        settings.save(None)

        self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data={"manage_rtb_sources_as_one": True},
            format="json",
        )

        args, kwargs = mock_ad_group_settings_update.call_args
        self.assertEqual(kwargs.get("state"), dash.constants.AdGroupSettingsState.INACTIVE)
        self.assertEqual(kwargs.get("b1_sources_group_enabled"), True)

    def test_put_deals(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign, name="Demo adgroup")

        settings = ad_group.get_current_settings().copy_settings()
        settings.ad_group_name = ad_group.name
        settings.notes = "adgroups notes"
        settings.redirect_pixel_urls = ["http://a.com/b.jpg", "http://a.com/c.jpg"]
        settings.redirect_javascript = "alert('a')"
        settings.save(None)

        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal_to_be_removed = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal_to_be_removed, adgroup=ad_group)

        deal_to_be_added = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)

        r = self.client.get(reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal_to_be_removed.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 1)

        put_data = resp_json["data"].copy()

        put_data["deals"] = [
            {
                "id": str(deal_to_be_added.id),
                "dealId": deal_to_be_added.deal_id,
                "source": deal_to_be_added.source.bidder_slug,
            }
        ]

        r = self.client.put(
            reverse("restapi.adgroup.internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal_to_be_added.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 1)
