from decimal import Decimal

from django.urls import reverse

import dash.models
from dash import constants
from restapi.common.views_base_test import RESTAPITest
from restapi.common.views_base_test import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class LegacyCampaignGoalsTest(RESTAPITest):
    @classmethod
    def campaigngoal_repr(
        cls, id=None, primary=True, type=constants.CampaignGoalKPI.TIME_ON_SITE, conversionGoal=None, value="30.0000"
    ):
        representation = {
            "id": id if id is not None else None,
            "primary": primary,
            "type": constants.CampaignGoalKPI.get_name(type),
            "conversionGoal": conversionGoal,
            "value": value,
        }
        return cls.normalize(representation)

    def validate_against_db(self, campaigngoal):
        campaigngoal_db = dash.models.CampaignGoal.objects.get(pk=campaigngoal["id"])
        conversiongoal_db = campaigngoal_db.conversion_goal
        expected_conversiongoal = None
        if conversiongoal_db:
            pixel_url = conversiongoal_db.pixel.get_url() if conversiongoal_db.pixel else None
            expected_conversiongoal = dict(
                goalId=conversiongoal_db.goal_id or str(conversiongoal_db.pixel.id),
                name=conversiongoal_db.name,
                pixelUrl=pixel_url,
                conversionWindow=constants.ConversionWindows.get_name(conversiongoal_db.conversion_window),
                type=constants.ConversionGoalType.get_name(conversiongoal_db.type),
            )

        rounding_format = "1.000" if campaigngoal_db.type == constants.CampaignGoalKPI.CPC else "1.00"
        expected = self.campaigngoal_repr(
            id=campaigngoal_db.id,
            primary=campaigngoal_db.primary,
            type=campaigngoal_db.type,
            conversionGoal=expected_conversiongoal,
            value=campaigngoal_db.values.last().value.quantize(Decimal(rounding_format)),
        )
        self.assertEqual(expected, campaigngoal)

    def test_campaigngoals_get(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(dash.models.Account, agency=agency)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        campaign_goal = magic_mixer.blend(dash.models.CampaignGoal, campaign=campaign, primary=True)
        campaign_goal.add_local_value(None, Decimal("0.15"), skip_history=True)

        r = self.client.get(
            reverse(
                "restapi.campaigngoal.v1:campaigngoals_details",
                kwargs={"campaign_id": campaign.id, "goal_id": campaign_goal.id},
            )
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_campaigngoals_get_no_permission(self):
        account = magic_mixer.blend(dash.models.Account)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        campaign_goal = magic_mixer.blend(dash.models.CampaignGoal, campaign=campaign, primary=True)
        campaign_goal.add_local_value(None, Decimal("0.15"), skip_history=True)

        r = self.client.get(
            reverse(
                "restapi.campaigngoal.v1:campaigngoals_details",
                kwargs={"campaign_id": campaign.id, "goal_id": campaign_goal.id},
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_campaigngoals_get_invalid(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(dash.models.Account, agency=agency)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )

        r = self.client.get(
            reverse(
                "restapi.campaigngoal.v1:campaigngoals_details", kwargs={"campaign_id": campaign.id, "goal_id": 1234}
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_campaigngoals_list(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(dash.models.Account, agency=agency)
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        campaign_goal_primary = magic_mixer.blend(dash.models.CampaignGoal, campaign=campaign, primary=True)
        campaign_goal_primary.add_local_value(None, Decimal("0.15"), skip_history=True)

        campaign_goals = magic_mixer.cycle(5).blend(dash.models.CampaignGoal, campaign=campaign, primary=False)
        for campaign_goal in campaign_goals:
            campaign_goal.add_local_value(None, Decimal("0.15"), skip_history=True)

        r = self.client.get(reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_campaigngoals_remove(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        campaign_goal = magic_mixer.blend(dash.models.CampaignGoal, campaign=campaign, primary=True)
        campaign_goal.add_local_value(None, Decimal("0.15"), skip_history=True)

        r = self.client.get(
            reverse(
                "restapi.campaigngoal.v1:campaigngoals_details",
                kwargs={"campaign_id": campaign.id, "goal_id": campaign_goal.id},
            )
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        r = self.client.delete(
            reverse(
                "restapi.campaigngoal.v1:campaigngoals_details",
                kwargs={"campaign_id": campaign.id, "goal_id": campaign_goal.id},
            )
        )
        self.assertEqual(r.status_code, 204)
        r = self.client.get(
            reverse(
                "restapi.campaigngoal.v1:campaigngoals_details",
                kwargs={"campaign_id": campaign.id, "goal_id": campaign_goal.id},
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_campaigngoals_put(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        campaign_goal = magic_mixer.blend(dash.models.CampaignGoal, campaign=campaign, primary=True)
        campaign_goal.add_local_value(None, Decimal("0.15"), skip_history=True)

        test_campaigngoal = self.campaigngoal_repr(id=campaign_goal.id, value="0.39", primary=True)
        r = self.client.put(
            reverse(
                "restapi.campaigngoal.v1:campaigngoals_details",
                kwargs={"campaign_id": campaign.id, "goal_id": campaign_goal.id},
            ),
            test_campaigngoal,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["value"], test_campaigngoal["value"])
        self.assertEqual(resp_json["data"]["primary"], test_campaigngoal["primary"])

    def test_campaigngoals_post(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )

        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPC, value="0.33", primary=True, conversionGoal=None
        )
        post_data = test_campaigngoal.copy()
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=post_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

    def test_campaigngoals_cpa_post(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=account)
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPA,
            value="0.44",
            primary=True,
            conversionGoal=dict(type="PIXEL", conversionWindow="LEQ_7_DAYS", goalId=pixel.id),
        )
        post_data = test_campaigngoal.copy()
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=post_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

    def test_campaigngoals_legacy_window_post(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=account)
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPA,
            value="0.44",
            primary=True,
            conversionGoal=dict(type="PIXEL", conversionWindow="LEQ_90_DAYS", goalId=pixel.id),
        )
        post_data = test_campaigngoal.copy()
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=post_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_campaigngoals_post_validation(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )

        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPC, value="0.33", conversionGoal=None
        )
        post_data = test_campaigngoal.copy()
        del post_data["primary"]
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=post_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        test_campaigngoal = self.campaigngoal_repr(value="0.33", primary=True, conversionGoal=None)
        post_data = test_campaigngoal.copy()
        del post_data["type"]
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=post_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        test_campaigngoal = self.campaigngoal_repr(type=constants.CampaignGoalKPI.CPC, conversionGoal=None)
        post_data = test_campaigngoal.copy()
        del post_data["value"]
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=post_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPC, value="0.33", primary=True, conversionGoal=None
        )
        post_data = test_campaigngoal.copy()
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=post_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

    def test_campaigngoals_same_type(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )

        test_campaigngoal = self.campaigngoal_repr(type=constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT)
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=test_campaigngoal,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=test_campaigngoal,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_campaigngoals_negative_value(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        campaign_goal = magic_mixer.blend(dash.models.CampaignGoal, campaign=campaign, primary=True)
        campaign_goal.add_local_value(None, Decimal("0.15"), skip_history=True)

        test_campaigngoal = self.campaigngoal_repr(id=campaign_goal.id, value="-10.00")
        r = self.client.put(
            reverse(
                "restapi.campaigngoal.v1:campaigngoals_details",
                kwargs={"campaign_id": campaign.id, "goal_id": campaign_goal.id},
            ),
            data=test_campaigngoal,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["value"], test_campaigngoal["value"])

    def test_campaigngoals_cpa_no_conversion_goal(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(
            dash.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )

        test_campaigngoal = self.campaigngoal_repr(type=constants.CampaignGoalKPI.CPA, conversionGoal=None)
        post_data = test_campaigngoal.copy()
        r = self.client.post(
            reverse("restapi.campaigngoal.v1:campaigngoals_list", kwargs={"campaign_id": campaign.id}),
            data=post_data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")


class CampaignGoalsTest(RESTAPITestCase, LegacyCampaignGoalsTest):
    pass
