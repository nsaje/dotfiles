from decimal import Decimal
import json
from mock import patch

from django.urls import reverse
from django.test import TestCase

from core.models import all_rtb
from dash import models

from zemauth.models import User
from utils.test_helper import add_permissions


class RTBSourceSettingsTest(TestCase):

    fixtures = ["test_api", "test_views", "test_non_superuser", "test_geolocations"]

    def setUp(self):
        self.ad_group = models.AdGroup.objects.get(id=2)
        new_ad_group_settings = self.ad_group.get_current_settings().copy_settings()
        new_ad_group_settings.b1_sources_group_enabled = True
        new_ad_group_settings.save(None)

        self.user = User.objects.get(id=1)

        self.assertFalse(self.user.is_superuser)

        for account in models.Account.objects.all():
            account.users.add(self.user)

        add_permissions(
            self.user,
            [
                "settings_view",
                "can_set_ad_group_max_cpc",
                "can_access_table_breakdowns_feature",
                "can_set_rtb_sources_as_one_cpc",
            ],
        )
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

    def test_validate_max_cpc(self):
        updated_ad_group_settings = self.ad_group.get_current_settings().copy_settings()
        updated_ad_group_settings.cpc_cc = Decimal("0.10")
        updated_ad_group_settings.save(None)

        response = self.client.post(
            reverse(
                "grid_ad_group_source_settings",
                kwargs={"ad_group_id": self.ad_group.id, "source_id": all_rtb.AllRTBSource.id},
            ),
            json.dumps({"settings": {"cpc_cc": "0.15"}}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)

        parsed = json.loads(response.content)
        self.assertFalse(parsed["success"])
        self.assertEqual("ValidationError", parsed["data"]["error_code"])
        self.assertTrue("b1_sources_group_cpc_cc" in parsed["data"]["errors"])
