import json
from decimal import Decimal

from django.urls import reverse
from mock import patch

from core.models import all_rtb
from dash import constants
from dash import models
from dash.common.views_base_test_case import DASHAPITestCase
from dash.common.views_base_test_case import FutureDASHAPITestCase
from utils.test_helper import add_permissions
from zemauth.models import User


class LegacyRTBSourceSettingsTestCase(DASHAPITestCase):

    fixtures = ["test_api", "test_views", "test_non_superuser", "test_geolocations"]

    def setUp(self):
        self.ad_group = models.AdGroup.objects.get(id=2)
        new_ad_group_settings = self.ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.b1_sources_group_enabled = True
        new_ad_group_settings.save(None)

        self.user = User.objects.get(id=1)

        self.assertFalse(self.user.is_superuser)

        add_permissions(self.user, ["can_set_rtb_sources_as_one_cpc", "fea_can_use_cpm_buying"])
        self.client.login(username=self.user.email, password="secret")

    @patch("utils.redirector_helper.insert_adgroup")
    def test_post_cpc(self, mock_redirector_insert_adgroup):
        prev_ad_group_settings = self.ad_group.get_current_settings()
        response = self.client.post(
            reverse(
                "grid_ad_group_source_settings",
                kwargs={"ad_group_id": self.ad_group.id, "source_id": all_rtb.AllRTBSource.id},
            ),
            json.dumps({"settings": {"cpc_cc": "0.15"}}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        parsed = json.loads(response.content)
        self.assertTrue(parsed["success"])

        next_ad_group_settings = models.AdGroup.objects.get(pk=2).get_current_settings()
        self.assertNotEqual(
            prev_ad_group_settings.b1_sources_group_cpc_cc, next_ad_group_settings.b1_sources_group_cpc_cc
        )
        self.assertNotEqual("0.15", next_ad_group_settings.b1_sources_group_cpc_cc)
        self.assertEqual(Decimal("0.15"), next_ad_group_settings.b1_sources_group_cpc_cc)

    def test_validate_max_source_cpc(self):
        updated_ad_group_settings = self.ad_group.get_current_settings().copy_settings()
        updated_ad_group_settings.cpc = Decimal("0.10")
        updated_ad_group_settings.save(None)

        response = self.client.post(
            reverse(
                "grid_ad_group_source_settings",
                kwargs={"ad_group_id": self.ad_group.id, "source_id": all_rtb.AllRTBSource.id},
            ),
            json.dumps({"settings": {"cpc_cc": "30.00"}}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)

        parsed = json.loads(response.content)
        self.assertFalse(parsed["success"])
        self.assertEqual("ValidationError", parsed["data"]["error_code"])
        self.assertTrue("Maximum CPC on RTB Sources is" in parsed["data"]["errors"]["b1_sources_group_cpc_cc"][0])

    @patch("utils.redirector_helper.insert_adgroup")
    def test_post_cpm(self, mock_redirector_insert_adgroup):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)
        prev_ad_group_settings = self.ad_group.get_current_settings()
        response = self.client.post(
            reverse(
                "grid_ad_group_source_settings",
                kwargs={"ad_group_id": self.ad_group.id, "source_id": all_rtb.AllRTBSource.id},
            ),
            json.dumps({"settings": {"cpm": "0.35"}}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        parsed = json.loads(response.content)
        self.assertTrue(parsed["success"])

        next_ad_group_settings = models.AdGroup.objects.get(pk=2).get_current_settings()
        self.assertNotEqual(prev_ad_group_settings.b1_sources_group_cpm, next_ad_group_settings.b1_sources_group_cpm)
        self.assertEqual(Decimal("0.35"), next_ad_group_settings.b1_sources_group_cpm)

    def test_validate_max_source_cpm(self):
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)
        updated_ad_group_settings = self.ad_group.get_current_settings().copy_settings()
        updated_ad_group_settings.cpm = Decimal("0.40")
        updated_ad_group_settings.save(None)

        response = self.client.post(
            reverse(
                "grid_ad_group_source_settings",
                kwargs={"ad_group_id": self.ad_group.id, "source_id": all_rtb.AllRTBSource.id},
            ),
            json.dumps({"settings": {"cpm": "26.00"}}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)

        parsed = json.loads(response.content)
        self.assertFalse(parsed["success"])
        self.assertEqual("ValidationError", parsed["data"]["error_code"])
        self.assertTrue("Maximum CPM on RTB Sources is" in parsed["data"]["errors"]["b1_sources_group_cpm"][0])


class RTBSourceSettingsTestCase(FutureDASHAPITestCase, LegacyRTBSourceSettingsTestCase):
    pass
