from decimal import Decimal

from django.urls import reverse

import dash.models
from dash import constants
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class CampaignGoalsTest(RESTAPITest):
    @classmethod
    def campaigngoal_repr(
        cls, id=2, primary=True, type=constants.CampaignGoalKPI.TIME_ON_SITE, conversionGoal=None, value="30.0000"
    ):
        representation = {
            "id": id,
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
        r = self.client.get(reverse("campaigngoals_details", kwargs={"campaign_id": 608, "goal_id": 1238}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_campaigngoals_list(self):
        r = self.client.get(reverse("campaigngoals_list", kwargs={"campaign_id": 608}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_campaigngoals_remove(self):
        r = self.client.get(reverse("campaigngoals_details", kwargs={"campaign_id": 608, "goal_id": 1238}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        r = self.client.delete(reverse("campaigngoals_details", kwargs={"campaign_id": 608, "goal_id": 1238}))
        self.assertEqual(r.status_code, 204)
        r = self.client.get(reverse("campaigngoals_details", kwargs={"campaign_id": 608, "goal_id": 1238}))
        resp_json = self.assertResponseError(r, "MissingDataError")

    def test_campaigngoals_put(self):
        test_campaigngoal = self.campaigngoal_repr(id=1238, value="0.39", primary=True)
        r = self.client.put(
            reverse("campaigngoals_details", kwargs={"campaign_id": 608, "goal_id": 1238}),
            test_campaigngoal,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["value"], test_campaigngoal["value"])
        self.assertEqual(resp_json["data"]["primary"], test_campaigngoal["primary"])

    def test_campaigngoals_post(self):
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPC, value="0.33", primary=True, conversionGoal=None
        )
        post_data = test_campaigngoal.copy()
        del post_data["id"]
        r = self.client.post(reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=post_data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

    def test_campaigngoals_cpa_post(self):
        account = dash.models.Account.objects.get(pk=186)
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=account)
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPA,
            value="0.44",
            primary=True,
            conversionGoal=dict(type="PIXEL", conversionWindow="LEQ_7_DAYS", goalId=pixel.id),
        )
        post_data = test_campaigngoal.copy()
        del post_data["id"]
        r = self.client.post(reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=post_data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

    def test_campaigngoals_legacy_window_post(self):
        account = dash.models.Account.objects.get(pk=186)
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=account)
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPA,
            value="0.44",
            primary=True,
            conversionGoal=dict(type="PIXEL", conversionWindow="LEQ_90_DAYS", goalId=pixel.id),
        )
        post_data = test_campaigngoal.copy()
        del post_data["id"]
        r = self.client.post(reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=post_data, format="json")
        self.assertResponseError(r, "ValidationError")

    def test_campaigngoals_post_validation(self):
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPC, value="0.33", conversionGoal=None
        )
        post_data = test_campaigngoal.copy()
        del post_data["id"]
        del post_data["primary"]
        r = self.client.post(reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=post_data, format="json")
        self.assertResponseError(r, "ValidationError")
        test_campaigngoal = self.campaigngoal_repr(value="0.33", primary=True, conversionGoal=None)
        post_data = test_campaigngoal.copy()
        del post_data["id"]
        del post_data["type"]
        r = self.client.post(reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=post_data, format="json")
        self.assertResponseError(r, "ValidationError")
        test_campaigngoal = self.campaigngoal_repr(type=constants.CampaignGoalKPI.CPC, conversionGoal=None)
        post_data = test_campaigngoal.copy()
        del post_data["id"]
        del post_data["value"]
        r = self.client.post(reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=post_data, format="json")
        self.assertResponseError(r, "ValidationError")
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPC, value="0.33", primary=True, conversionGoal=None
        )
        post_data = test_campaigngoal.copy()
        del post_data["id"]
        r = self.client.post(reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=post_data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

    def test_campaigngoals_same_type(self):
        test_campaigngoal = self.campaigngoal_repr(type=constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT)
        del test_campaigngoal["id"]
        r = self.client.post(
            reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=test_campaigngoal, format="json"
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        r = self.client.post(
            reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=test_campaigngoal, format="json"
        )
        self.assertResponseError(r, "ValidationError")

    def test_campaigngoals_negative_value(self):
        test_campaigngoal = self.campaigngoal_repr(id=1238, value="-10.00")
        r = self.client.put(
            reverse("campaigngoals_details", kwargs={"campaign_id": 608, "goal_id": 1238}),
            data=test_campaigngoal,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["value"], test_campaigngoal["value"])

    def test_cpa_no_conversion_goal(self):
        test_campaigngoal = self.campaigngoal_repr(type=constants.CampaignGoalKPI.CPA, conversionGoal=None)
        post_data = test_campaigngoal.copy()
        del post_data["id"]
        r = self.client.post(reverse("campaigngoals_list", kwargs={"campaign_id": 608}), data=post_data, format="json")
        self.assertResponseError(r, "ValidationError")
