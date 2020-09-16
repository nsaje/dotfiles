import json

import mock
from django.urls import reverse

import core.models
import dash.models
import restapi.serializers
import utils.dates_helper
import utils.test_helper
from automation import autopilot
from dash import constants
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class CampaignViewSetTest(RESTAPITestCase):
    @classmethod
    def campaign_repr(
        cls,
        id=None,
        account_id=None,
        archived=False,
        autopilot=False,
        iab_category=constants.IABCategory.IAB1_1,
        language=constants.Language.ENGLISH,
        type=constants.CampaignType.CONTENT,
        name="My Campaign TEST",
        enable_ga_tracking=True,
        ga_tracking_type=constants.GATrackingType.EMAIL,
        ga_property_id="",
        enable_adobe_tracking=False,
        adobe_tracking_param="cid",
        whitelist_publisher_groups=[],
        blacklist_publisher_groups=[],
        target_devices=[constants.AdTargetDevice.DESKTOP],
        target_environments=[constants.AdTargetEnvironment.APP],
        target_os=[{"name": constants.OperatingSystem.ANDROID}, {"name": constants.OperatingSystem.LINUX}],
        frequency_capping=None,
    ):
        representation = {
            "id": str(id) if id is not None else None,
            "accountId": str(account_id) if account_id is not None else None,
            "archived": archived,
            "autopilot": autopilot,
            "iabCategory": constants.IABCategory.get_name(iab_category),
            "language": constants.Language.get_name(language),
            "type": constants.CampaignType.get_name(type),
            "name": name,
            "tracking": {
                "ga": {
                    "enabled": enable_ga_tracking,
                    "type": constants.GATrackingType.get_name(ga_tracking_type),
                    "webPropertyId": ga_property_id,
                },
                "adobe": {"enabled": enable_adobe_tracking, "trackingParameter": adobe_tracking_param},
            },
            "targeting": {
                "devices": restapi.serializers.targeting.DevicesSerializer(target_devices).data,
                "environments": restapi.serializers.targeting.EnvironmentsSerializer(target_environments).data,
                "os": restapi.serializers.targeting.OSsSerializer(target_os).data,
                "publisherGroups": {"included": whitelist_publisher_groups, "excluded": blacklist_publisher_groups},
            },
            "frequencyCapping": frequency_capping,
        }
        return cls.normalize(representation)

    def validate_against_db(self, campaign):
        campaign_db = dash.models.Campaign.objects.get(pk=campaign["id"])
        settings_db = campaign_db.settings
        expected = self.campaign_repr(
            id=campaign_db.id,
            account_id=campaign_db.account_id,
            archived=settings_db.archived,
            autopilot=settings_db.autopilot,
            iab_category=settings_db.iab_category,
            language=settings_db.language,
            type=campaign_db.type,
            name=settings_db.name,
            enable_ga_tracking=settings_db.enable_ga_tracking,
            ga_tracking_type=settings_db.ga_tracking_type,
            ga_property_id=settings_db.ga_property_id,
            enable_adobe_tracking=settings_db.enable_adobe_tracking,
            adobe_tracking_param=settings_db.adobe_tracking_param,
            whitelist_publisher_groups=settings_db.whitelist_publisher_groups,
            blacklist_publisher_groups=settings_db.blacklist_publisher_groups,
            target_devices=settings_db.target_devices,
            target_environments=settings_db.target_environments,
            target_os=settings_db.target_os,
            frequency_capping=settings_db.frequency_capping,
        )
        # TODO: PLAC: remove after legacy grace period
        expected["targeting"]["placements"] = expected["targeting"]["environments"]
        self.assertEqual(expected, campaign)

    def test_campaigns_get(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        campaign = magic_mixer.blend(core.models.Campaign, account=account, type=dash.constants.CampaignType.CONTENT)
        r = self.client.get(reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_campaigns_put(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account, type=dash.constants.CampaignType.CONTENT)
        test_campaign = self.campaign_repr(
            id=campaign.id, account_id=account.id, name="My test campaign!", frequency_capping=33
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=test_campaign,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        # TODO: PLAC: remove after legacy grace period
        test_campaign["targeting"]["placements"] = test_campaign["targeting"]["environments"]
        self.assertEqual(resp_json["data"], test_campaign)

    def test_campaigns_put_empty(self):
        put_data = {}
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account, type=dash.constants.CampaignType.CONTENT)
        settings_count = dash.models.CampaignSettings.objects.filter(campaign_id=campaign.id).count()
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(settings_count, dash.models.CampaignSettings.objects.filter(campaign_id=campaign.id).count())

    @mock.patch.object(autopilot, "recalculate_budgets_campaign", autospec=True)
    def test_campaigns_put_autopilot(self, mock_autopilot):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, type=dash.constants.CampaignType.CONTENT, autopilot=False
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data={"autopilot": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["autopilot"], True)

    def test_campaigns_put_archive_restore(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, type=dash.constants.CampaignType.CONTENT, archived=False
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data={"archived": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["archived"], True)

        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data={"archived": False},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["archived"], False)

    # TODO: PLAC: remove after legacy grace period
    def test_campaign_put_environment_targeting_legacy(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account, type=dash.constants.CampaignType.CONTENT)
        campaign.settings.update_unsafe(None, target_environments=None)

        self.assertIsNone(campaign.settings.target_environments)

        campaign_data = self.campaign_repr(id=campaign.id, account_id=account.id)
        del campaign_data["targeting"]["environments"]
        campaign_data["targeting"]["placements"] = ["SITE"]
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=campaign_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(["SITE"], resp_json["data"]["targeting"]["environments"])
        self.assertEqual(["SITE"], resp_json["data"]["targeting"]["placements"])
        del resp_json["data"]["targeting"]["placements"]
        campaign.refresh_from_db()
        self.assertEqual([dash.constants.AdTargetEnvironment.SITE], campaign.settings.target_environments)

        campaign_data = self.campaign_repr(
            id=campaign.id, account_id=account.id, target_environments=[constants.Environment.APP]
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=campaign_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(["APP"], resp_json["data"]["targeting"]["environments"])
        self.assertEqual(["APP"], resp_json["data"]["targeting"]["placements"])
        del resp_json["data"]["targeting"]["placements"]
        campaign.refresh_from_db()
        self.assertEqual([dash.constants.AdTargetEnvironment.APP], campaign.settings.target_environments)

        campaign_data = self.campaign_repr(id=campaign.id, account_id=account.id)
        campaign_data["targeting"]["environments"] = ["APP"]
        campaign_data["targeting"]["placements"] = ["SITE"]
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=campaign_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(["APP"], resp_json["data"]["targeting"]["environments"])
        self.assertEqual(["APP"], resp_json["data"]["targeting"]["placements"])
        del resp_json["data"]["targeting"]["placements"]
        campaign.refresh_from_db()
        self.assertEqual([dash.constants.AdTargetEnvironment.APP], campaign.settings.target_environments)

        campaign_data = self.campaign_repr(
            id=campaign.id, account_id=account.id, target_environments=[constants.Environment.SITE]
        )
        campaign_data["targeting"]["placements"] = ["SITE"]
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=campaign_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(["SITE"], resp_json["data"]["targeting"]["environments"])
        self.assertEqual(["SITE"], resp_json["data"]["targeting"]["placements"])
        del resp_json["data"]["targeting"]["placements"]
        campaign.refresh_from_db()
        self.assertEqual([dash.constants.AdTargetEnvironment.SITE], campaign.settings.target_environments)

    def test_campaigns_list(self):
        account = self.mix_account(user=self.user, permissions=[Permission.READ])
        account_no_access = magic_mixer.blend(core.models.Account)
        campaigns = magic_mixer.cycle(5).blend(core.models.Campaign, account=account)
        campaigns_no_access = magic_mixer.cycle(5).blend(core.models.Campaign, account=account_no_access)

        r = self.client.get(reverse("restapi.campaign.v1:campaigns_list"))
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_ids = [x.get("id") for x in resp_json["data"]]
        for item in campaigns:
            self.assertTrue(str(item.id) in resp_json_ids)
        for item in campaigns_no_access:
            self.assertTrue(str(item.id) not in resp_json_ids)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_campaigns_list_invalid_params(self):
        r = self.client.get(
            reverse("restapi.campaign.v1:campaigns_list"),
            {"accountId": "NON-NUMERICAL", "offset": "NON-NUMERICAL", "limit": "NON-NUMERICAL"},
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            {"accountId": ["Invalid format"], "offset": ["Invalid format"], "limit": ["Invalid format"]},
            resp_json["details"],
        )

    def test_campaigns_list_permissionless(self):
        utils.test_helper.remove_permissions(self.user, permissions=["can_set_frequency_capping"])
        account = self.mix_account(user=self.user, permissions=[Permission.READ])
        magic_mixer.cycle(5).blend(core.models.Campaign, account=account)
        r = self.client.get(reverse("restapi.campaign.v1:campaigns_list"))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.assertFalse("frequencyCapping" in item)
            item["frequencyCapping"] = None
            self.validate_against_db(item)

    def test_campaigns_list_account_id(self):
        account = self.mix_account(user=self.user, permissions=[Permission.READ])
        magic_mixer.cycle(5).blend(core.models.Campaign, account=account)
        r = self.client.get(reverse("restapi.campaign.v1:campaigns_list"), data={"accountId": account.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)
            self.assertEqual(int(item["accountId"]), account.id)

    def test_campaigns_list_only_non_paginated_ids(self):
        account = self.mix_account(user=self.user, permissions=[Permission.READ])
        magic_mixer.cycle(5).blend(core.models.Campaign, account=account)

        r = self.client.get(reverse("restapi.campaign.v1:campaigns_list"))
        resp_json = self.assertResponseValid(r, data_type=list)

        r_only_non_paginated_ids = self.client.get(
            reverse("restapi.campaign.v1:campaigns_list"), data={"onlyNonPaginatedIds": True}
        )
        resp_json_only_non_paginated_ids = self.assertResponseValid(r_only_non_paginated_ids, data_type=list)

        self.assertEqual(
            [{"id": campaign["id"]} for campaign in resp_json["data"]], resp_json_only_non_paginated_ids["data"]
        )

    def test_campaigns_list_exclude_inactive(self):
        account = self.mix_account(user=self.user, permissions=[Permission.READ])
        campaigns = magic_mixer.cycle(5).blend(core.models.Campaign, account=account)
        active_adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaigns[0])

        r_no_active = self.client.get(reverse("restapi.campaign.v1:campaigns_list"), data={"excludeInactive": True})
        resp_json_no_active = self.assertResponseValid(r_no_active, data_type=list)
        self.assertEqual(len(resp_json_no_active["data"]), 0)

        active_adgroup.settings.update_unsafe(
            None,
            state=constants.AdGroupSettingsState.ACTIVE,
            start_date=utils.dates_helper.local_yesterday(),
            end_date=utils.dates_helper.days_after(utils.dates_helper.local_today(), 5),
        )

        r_one_active = self.client.get(reverse("restapi.campaign.v1:campaigns_list"), data={"excludeInactive": True})
        resp_json_one_active = self.assertResponseValid(r_one_active, data_type=list)

        self.assertEqual(len(resp_json_one_active["data"]), 1)
        self.assertEqual(str(campaigns[0].id), str(resp_json_one_active["data"][0].get("id")))

    def test_campaigns_list_account_id_invalid(self):
        account = magic_mixer.blend(core.models.Account)
        r = self.client.get(reverse("restapi.campaign.v1:campaigns_list"), data={"accountId": account.id})
        self.assertResponseError(r, "MissingDataError")

    def test_campaigns_list_pagination(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        magic_mixer.cycle(10).blend(dash.models.Campaign, account=account)
        r = self.client.get(reverse("restapi.campaign.v1:campaigns_list"), {"accountId": account.id})
        r_paginated = self.client.get(
            reverse("restapi.campaign.v1:campaigns_list"), {"accountId": account.id, "limit": 2, "offset": 5}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json["data"][5:7], resp_json_paginated["data"])

    def test_campaigns_list_exclude_archived(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        magic_mixer.cycle(3).blend(dash.models.Campaign, account=account, archived=False)
        magic_mixer.cycle(2).blend(dash.models.Campaign, account=account, archived=True)
        r = self.client.get(reverse("restapi.campaign.v1:campaigns_list"), {"accountId": account.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(3, len(resp_json["data"]))
        for item in resp_json["data"]:
            self.validate_against_db(item)
            self.assertFalse(item["archived"])

    def test_campaigns_list_include_archived(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        magic_mixer.cycle(3).blend(dash.models.Campaign, account=account, archived=False)
        magic_mixer.cycle(2).blend(dash.models.Campaign, account=account, archived=True)
        r = self.client.get(
            reverse("restapi.campaign.v1:campaigns_list"), {"accountId": account.id, "includeArchived": "true"}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(5, len(resp_json["data"]))
        for item in resp_json["data"]:
            self.validate_against_db(item)

    @mock.patch("automation.autopilot.recalculate_budgets_campaign")
    @mock.patch("utils.email_helper.send_campaign_created_email")
    def test_campaigns_post(self, mock_send, mock_autopilot):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        new_campaign = self.campaign_repr(
            account_id=account.id, name="All About Testing", type=constants.CampaignType.VIDEO, frequency_capping=33
        )
        r = self.client.post(reverse("restapi.campaign.v1:campaigns_list"), data=new_campaign, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_campaign["id"] = resp_json["data"]["id"]
        # TODO: PLAC: remove after legacy grace period
        new_campaign["targeting"]["placements"] = new_campaign["targeting"]["environments"]
        self.assertEqual(resp_json["data"], new_campaign)
        self.assertEqual(resp_json["data"]["type"], constants.CampaignType.get_name(constants.CampaignType.VIDEO))
        mock_send.assert_not_called()

    @mock.patch("automation.autopilot.recalculate_budgets_campaign")
    @mock.patch("utils.email_helper.send_campaign_created_email")
    def test_campaigns_post_account_archived(self, mock_send, mock_autopilot):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], archived=True)
        new_campaign = self.campaign_repr(
            account_id=account.id,
            name="All About Testing",
            type=constants.CampaignType.VIDEO,
            whitelist_publisher_groups=[153, 154],
            blacklist_publisher_groups=[],
            frequency_capping=33,
        )
        r = self.client.post(reverse("restapi.campaign.v1:campaigns_list"), data=new_campaign, format="json")
        self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            ["Can not create a campaign on an archived account."], json.loads(r.content)["details"]["accountId"]
        )
        mock_send.assert_not_called()

    @mock.patch("automation.autopilot.recalculate_budgets_campaign")
    def test_campaigns_post_no_type(self, mock_autopilot):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        new_campaign = self.campaign_repr(account_id=account.id, name="All About Testing", frequency_capping=33)
        del new_campaign["type"]
        r = self.client.post(reverse("restapi.campaign.v1:campaigns_list"), data=new_campaign, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_campaign["id"] = resp_json["data"]["id"]
        new_campaign["type"] = resp_json["data"]["type"]
        # TODO: PLAC: remove after legacy grace period
        new_campaign["targeting"]["placements"] = new_campaign["targeting"]["environments"]
        self.assertEqual(resp_json["data"], new_campaign)
        self.assertEqual(resp_json["data"]["type"], constants.CampaignType.get_name(constants.CampaignType.CONTENT))

    def test_campaigns_post_no_account_id(self):
        new_campaign = self.campaign_repr(
            name="Its me, Account", whitelist_publisher_groups=[], blacklist_publisher_groups=[]
        )
        r = self.client.post(reverse("restapi.campaign.v1:campaigns_list"), data=new_campaign, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_campaigns_post_wrong_account_id(self):
        account = magic_mixer.blend(core.models.Account)
        new_campaign = self.campaign_repr(
            account_id=account.id, name="Over 9000", whitelist_publisher_groups=[], blacklist_publisher_groups=[]
        )
        r = self.client.post(reverse("restapi.campaign.v1:campaigns_list"), data=new_campaign, format="json")
        self.assertResponseError(r, "MissingDataError")

    def test_iab_tier_1(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        test_campaign = self.campaign_repr(
            id=campaign.id, account_id=account.id, name="My test campaign!", iab_category=constants.IABCategory.IAB21
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=test_campaign,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_ga_property_id_validation(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        test_campaign = self.campaign_repr(
            id=campaign.id, account_id=account.id, name="My test campaign!", ga_property_id="PID"
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=test_campaign,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adobe_tracking_parameter_blank(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        test_campaign = self.campaign_repr(
            id=campaign.id, account_id=account.id, name="Adobe tracking campaign", adobe_tracking_param=""
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=test_campaign,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_campaigns_publisher_groups(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        account_no_access = magic_mixer.blend(core.models.Account)

        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        pg_one = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)
        pg_two = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account)
        pg_no_access = magic_mixer.blend(core.features.publisher_groups.PublisherGroup, account=account_no_access)

        test_campaign = self.campaign_repr(
            id=campaign.id,
            account_id=account.id,
            whitelist_publisher_groups=[pg_one.id],
            blacklist_publisher_groups=[pg_two.id],
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=test_campaign,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

        test_campaign = self.campaign_repr(
            id=campaign.id, account_id=account.id, whitelist_publisher_groups=[pg_no_access.id]
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=test_campaign,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        test_campaign = self.campaign_repr(
            id=campaign.id, account_id=account.id, blacklist_publisher_groups=[pg_no_access.id]
        )
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=test_campaign,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_type_validation(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account, type=constants.CampaignType.VIDEO)
        magic_mixer.blend(dash.models.AdGroup, campaign=campaign)
        test_campaign = self.campaign_repr(id=campaign.id, account_id=account.id, type=constants.CampaignType.DISPLAY)
        r = self.client.put(
            reverse("restapi.campaign.v1:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=test_campaign,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
