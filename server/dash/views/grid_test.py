import json
from decimal import Decimal

from django.urls import reverse

from core.models import all_rtb
from dash import constants
from dash import models
from utils.base_test_case import BaseTestCase
from zemauth.models import User


class RTBSourceSettingsTestCase(BaseTestCase):

    fixtures = ["test_api", "test_views", "test_non_superuser", "test_geolocations"]

    def setUp(self):
        self.ad_group = models.AdGroup.objects.get(id=2)
        new_ad_group_settings = self.ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.b1_sources_group_enabled = True
        new_ad_group_settings.save(None)

        self.user = User.objects.get(id=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password="secret")

    def test_post_cpc(self):
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
        # RTB cpc is mapped to ad group cpc
        self.assertTrue("CPC can't be higher than" in parsed["data"]["errors"]["b1_sources_group_cpc_cc"][0])

    def test_post_cpm(self):
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
        # RTB cpm is mapped to ad group cpm
        self.assertTrue("CPM can't be higher than" in parsed["data"]["errors"]["b1_sources_group_cpm"][0])
