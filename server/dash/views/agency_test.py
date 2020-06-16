# -*- coding: utf-8 -*-
import datetime
import http.client
import json

from django.conf import settings
from django.contrib.auth import models as authmodels
from django.contrib.auth.models import Permission
from django.core import mail
from django.http.request import HttpRequest
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from mock import ANY
from mock import patch

from core.features import history
from dash import constants
from dash import history_helpers
from dash import models
from dash.views import agency
from utils import exc
from utils.magic_mixer import magic_mixer
from utils.test_helper import add_permissions
from utils.test_helper import fake_request
from zemauth.models import User


class AdGroupSettingsStateTest(TestCase):
    fixtures = ["test_models.yaml", "test_adgroup_settings_state.yaml", "test_non_superuser.yaml", "test_geolocations"]

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        self.client.login(username=self.user.email, password="secret")

    def test_get(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ["can_control_ad_group_state_in_table"])
        response = self.client.get(reverse("ad_group_settings_state", kwargs={"ad_group_id": ad_group.id}), follow=True)

        self.assertDictEqual(
            json.loads(response.content),
            {"data": {"id": str(ad_group.pk), "state": ad_group.get_current_settings().state}, "success": True},
        )

    @patch("dash.dashapi.data_helper.campaign_has_available_budget")
    @patch("utils.k1_helper.update_ad_group")
    def test_activate(self, mock_k1_ping, mock_budget_check):
        ad_group = models.AdGroup.objects.get(pk=2)
        mock_budget_check.return_value = True

        # ensure this campaign has a goal
        models.CampaignGoal.objects.create_unsafe(campaign_id=ad_group.campaign_id)

        add_permissions(self.user, ["can_control_ad_group_state_in_table"])
        response = self.client.post(
            reverse("ad_group_settings_state", kwargs={"ad_group_id": ad_group.id}),
            json.dumps({"state": 1}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.ACTIVE)
        mock_k1_ping.assert_called_once_with(ad_group, msg="AdGroupSettings.put", priority=ANY)

    @patch("dash.dashapi.data_helper.campaign_has_available_budget")
    @patch("utils.k1_helper.update_ad_group")
    def test_activate_already_activated(self, mock_k1_ping, mock_budget_check):
        ad_group = models.AdGroup.objects.get(pk=1)
        mock_budget_check.return_value = True

        # ensure this campaign has a goal
        models.CampaignGoal.objects.create_unsafe(campaign_id=ad_group.campaign_id)

        add_permissions(self.user, ["can_control_ad_group_state_in_table"])
        response = self.client.post(
            reverse("ad_group_settings_state", kwargs={"ad_group_id": ad_group.id}),
            json.dumps({"state": 1}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(mock_k1_ping.called)

    @patch("utils.k1_helper.update_ad_group")
    def test_activate_without_budget(self, mock_k1_ping):
        ad_group = models.AdGroup.objects.get(pk=2)

        add_permissions(self.user, ["can_control_ad_group_state_in_table"])
        response = self.client.post(
            reverse("ad_group_settings_state", kwargs={"ad_group_id": ad_group.id}),
            json.dumps({"state": 1}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.INACTIVE)
        self.assertFalse(mock_k1_ping.called)

    @patch("dash.dashapi.data_helper.campaign_has_available_budget")
    @patch("utils.k1_helper.update_ad_group")
    def test_activate_no_goals(self, mock_k1_ping, mock_budget_check):
        ad_group = models.AdGroup.objects.get(pk=2)
        mock_budget_check.return_value = True

        add_permissions(self.user, ["can_control_ad_group_state_in_table"])
        response = self.client.post(
            reverse("ad_group_settings_state", kwargs={"ad_group_id": ad_group.id}),
            json.dumps({"state": 1}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(response.status_code, 400)

    @patch("utils.k1_helper.update_ad_group")
    def test_inactivate(self, mock_k1_ping):
        ad_group = models.AdGroup.objects.get(pk=1)

        add_permissions(self.user, ["can_control_ad_group_state_in_table"])
        response = self.client.post(
            reverse("ad_group_settings_state", kwargs={"ad_group_id": ad_group.id}),
            json.dumps({"state": 2}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.INACTIVE)
        mock_k1_ping.assert_called_once_with(ad_group, msg="AdGroupSettings.put", priority=ANY)

    def test_inactivate_already_inactivated(self):
        ad_group = models.AdGroup.objects.get(pk=2)
        add_permissions(self.user, ["can_control_ad_group_state_in_table"])
        response = self.client.post(
            reverse("ad_group_settings_state", kwargs={"ad_group_id": ad_group.id}),
            json.dumps({"state": 2}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)


class ConversionPixelTestCase(TestCase):
    fixtures = ["test_api.yaml", "test_views.yaml", "test_non_superuser.yaml", "test_conversion_pixel.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password="secret")

    def test_get(self):
        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        response = self.client.get(reverse("account_conversion_pixels", kwargs={"account_id": account.id}), follow=True)

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response["success"])
        self.assertCountEqual(
            [
                {
                    "id": 1,
                    "name": "test",
                    "url": settings.CONVERSION_PIXEL_PREFIX + "1/test/",
                    "archived": False,
                    "audience_enabled": True,
                    "additional_pixel": False,
                },
                {
                    "id": 2,
                    "name": "test2",
                    "url": settings.CONVERSION_PIXEL_PREFIX + "1/test2/",
                    "archived": False,
                    "audience_enabled": False,
                    "additional_pixel": False,
                },
            ],
            decoded_response["data"]["rows"],
        )

    def test_get_additional(self):
        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        p = models.ConversionPixel.objects.get(pk=2)
        p.additional_pixel = True
        p.save()

        response = self.client.get(reverse("account_conversion_pixels", kwargs={"account_id": account.id}), follow=True)

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response["success"])
        self.assertCountEqual(
            [
                {
                    "id": 1,
                    "name": "test",
                    "url": settings.CONVERSION_PIXEL_PREFIX + "1/test/",
                    "archived": False,
                    "audience_enabled": True,
                    "additional_pixel": False,
                },
                {
                    "id": 2,
                    "name": "test2",
                    "url": settings.CONVERSION_PIXEL_PREFIX + "1/test2/",
                    "archived": False,
                    "audience_enabled": False,
                    "additional_pixel": True,
                },
            ],
            decoded_response["data"]["rows"],
        )

    def test_get_non_existing_account(self):
        response = self.client.get(reverse("account_conversion_pixels", kwargs={"account_id": 9876}), follow=True)

        self.assertEqual(404, response.status_code)

    def test_get_redirect_url(self):
        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        permission = authmodels.Permission.objects.get(codename="can_redirect_pixels")
        self.user.user_permissions.add(permission)

        response = self.client.get(reverse("account_conversion_pixels", kwargs={"account_id": account.id}), follow=True)

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response["success"])
        self.assertCountEqual(
            [
                {
                    "id": 1,
                    "name": "test",
                    "url": settings.CONVERSION_PIXEL_PREFIX + "1/test/",
                    "archived": False,
                    "audience_enabled": True,
                    "additional_pixel": False,
                    "redirect_url": None,
                },
                {
                    "id": 2,
                    "name": "test2",
                    "url": settings.CONVERSION_PIXEL_PREFIX + "1/test2/",
                    "archived": False,
                    "audience_enabled": False,
                    "additional_pixel": False,
                    "redirect_url": None,
                },
            ],
            decoded_response["data"]["rows"],
        )

    def test_get_notes(self):
        account = models.Account.objects.get(pk=1)
        account.users.add(self.user)

        pixel = models.ConversionPixel.objects.get(pk=1)
        pixel.notes = "test note"
        pixel.save()

        permission = authmodels.Permission.objects.get(codename="can_see_pixel_notes")
        self.user.user_permissions.add(permission)

        response = self.client.get(reverse("account_conversion_pixels", kwargs={"account_id": account.id}), follow=True)

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response["success"])
        self.assertCountEqual(
            [
                {
                    "id": 1,
                    "name": "test",
                    "url": settings.CONVERSION_PIXEL_PREFIX + "1/test/",
                    "archived": False,
                    "audience_enabled": True,
                    "additional_pixel": False,
                    "notes": "test note",
                },
                {
                    "id": 2,
                    "name": "test2",
                    "url": settings.CONVERSION_PIXEL_PREFIX + "1/test2/",
                    "archived": False,
                    "audience_enabled": False,
                    "additional_pixel": False,
                    "notes": "",
                },
            ],
            decoded_response["data"]["rows"],
        )

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.k1_helper.update_account")
    def test_post(self, ping_mock, redirector_mock):
        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name"}),
            content_type="application/json",
            follow=True,
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response["success"])
        self.assertDictEqual(
            {
                "id": 3,
                "name": "name",
                "url": settings.CONVERSION_PIXEL_PREFIX + "1/3/",
                "archived": False,
                "audience_enabled": False,
                "additional_pixel": False,
            },
            decoded_response["data"],
        )

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE, hist.action_type)
        self.assertEqual("Created a conversion pixel named name.", hist.changes_text)
        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE, hist.action_type)

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.k1_helper.update_account")
    def test_post_audience_enabled(self, ping_mock, redirector_mock):
        audience_enabled_pixels = models.ConversionPixel.objects.filter(audience_enabled=True).filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))
        audience_enabled_pixels[0].audience_enabled = False
        audience_enabled_pixels[0].save()

        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name", "audience_enabled": True}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        audience_enabled_pixels = models.ConversionPixel.objects.filter(audience_enabled=True).filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))
        self.assertEqual(audience_enabled_pixels[0].name, "name")

        self.assertDictEqual(
            {
                "data": {
                    "id": audience_enabled_pixels[0].id,
                    "name": "name",
                    "archived": False,
                    "audience_enabled": True,
                    "additional_pixel": False,
                    "url": "https://p1.zemanta.com/p/1/{}/".format(audience_enabled_pixels[0].slug),
                },
                "success": True,
            },
            json.loads(response.content),
        )

        ping_mock.assert_called_once_with(models.Account.objects.get(pk=1), msg="conversion_pixel.create")
        self.assertFalse(redirector_mock.called)

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.k1_helper.update_account")
    def test_post_audience_enabled_invalid(self, ping_mock, redirector_mock):
        audience_enabled_pixels = models.ConversionPixel.objects.filter(audience_enabled=True).filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))

        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name", "audience_enabled": True}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertDictEqual(
            {
                "data": {
                    "error_code": "ValidationError",
                    "message": None,
                    "errors": {
                        "audience_enabled": "This pixel can not be used for building custom audiences because another pixel is already used: test."
                    },
                    "data": None,
                },
                "success": False,
            },
            json.loads(response.content),
        )

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)

        audience_enabled_pixels = models.ConversionPixel.objects.filter(audience_enabled=True).filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))

    @patch("utils.redirector_helper.update_pixel")
    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.k1_helper.update_account")
    def test_post_redirect_url(self, ping_mock, redirector_mock, update_pixel_mock):
        permission = authmodels.Permission.objects.get(codename="can_redirect_pixels")
        self.user.user_permissions.add(permission)

        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name", "redirect_url": "http://test.com"}),
            content_type="application/json",
            follow=True,
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response["success"])
        self.assertDictEqual(
            {
                "id": decoded_response["data"]["id"],
                "name": "name",
                "url": settings.CONVERSION_PIXEL_PREFIX + "1/{}/".format(decoded_response["data"]["id"]),
                "archived": False,
                "audience_enabled": False,
                "additional_pixel": False,
                "redirect_url": "http://test.com",
            },
            decoded_response["data"],
        )

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE, hist.action_type)
        self.assertEqual("Created a conversion pixel named name.", hist.changes_text)
        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE, hist.action_type)

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)

        self.assertTrue(update_pixel_mock.called)

    def test_post_redirect_url_invalid(self):
        permission = authmodels.Permission.objects.get(codename="can_redirect_pixels")
        self.user.user_permissions.add(permission)

        pixels_before = list(models.ConversionPixel.objects.all())

        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name", "redirect_url": "invalidurl"}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

    def test_post_name_empty(self):
        pixels_before = list(models.ConversionPixel.objects.all())

        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": ""}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

    def test_post_name_too_long(self):
        pixels_before = list(models.ConversionPixel.objects.all())

        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "a" * (models.ConversionPixel._meta.get_field("name").max_length + 1)}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual(list(models.ConversionPixel.objects.all()), pixels_before)

    @patch("utils.redirector_helper.update_pixel")
    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.k1_helper.update_account")
    def test_post_notes(self, ping_mock, redirector_mock, update_pixel_mock):
        permission = authmodels.Permission.objects.get(codename="can_see_pixel_notes")
        self.user.user_permissions.add(permission)
        conversion_pixel = models.ConversionPixel.objects.get(id=1)
        conversion_pixel.audience_enabled = False
        conversion_pixel.save()
        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name", "notes": "test notes"}),
            content_type="application/json",
            follow=True,
        )

        decoded_response = json.loads(response.content)
        self.assertEqual(200, response.status_code)
        self.assertTrue(decoded_response["success"])
        self.assertDictEqual(
            {
                "id": decoded_response["data"]["id"],
                "name": "name",
                "url": settings.CONVERSION_PIXEL_PREFIX + "1/{}/".format(decoded_response["data"]["id"]),
                "archived": False,
                "audience_enabled": False,
                "additional_pixel": False,
                "notes": "test notes",
            },
            decoded_response["data"],
        )

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE, hist.action_type)
        self.assertEqual("Created a conversion pixel named name.", hist.changes_text)
        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE, hist.action_type)

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)
        self.assertTrue(update_pixel_mock.called)

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.k1_helper.update_account")
    def test_put_audience_enabled(self, ping_mock, redirector_mock):
        existing_audience_enabled_pixels = models.ConversionPixel.objects.filter(audience_enabled=True).filter(
            account_id=1
        )
        self.assertEqual(1, len(existing_audience_enabled_pixels))
        existing_audience_enabled_pixels[0].audience_enabled = False
        existing_audience_enabled_pixels[0].save()

        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": existing_audience_enabled_pixels[0].id}),
            json.dumps({"audience_enabled": True}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        audience_enabled_pixels = models.ConversionPixel.objects.filter(audience_enabled=True).filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))
        self.assertEqual(audience_enabled_pixels[0].id, existing_audience_enabled_pixels[0].id)

        self.assertDictEqual(
            {
                "data": {
                    "id": audience_enabled_pixels[0].id,
                    "name": "test",
                    "archived": False,
                    "audience_enabled": True,
                    "additional_pixel": False,
                    "url": "https://p1.zemanta.com/p/1/{}/".format(audience_enabled_pixels[0].slug),
                },
                "success": True,
            },
            json.loads(response.content),
        )

        ping_mock.assert_called_once_with(models.Account.objects.get(pk=1), msg="conversion_pixel.update")
        self.assertEqual(redirector_mock.call_count, 4)

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.k1_helper.update_account")
    def test_put_audience_enabled_invalid(self, ping_mock, redirector_mock):
        existing_audience_enabled_pixels = models.ConversionPixel.objects.filter(audience_enabled=True).filter(
            account_id=1
        )
        self.assertEqual(1, len(existing_audience_enabled_pixels))

        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 2}),
            json.dumps({"name": "name", "audience_enabled": True}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertDictEqual(
            {
                "data": {
                    "error_code": "ValidationError",
                    "message": None,
                    "errors": {
                        "audience_enabled": "This pixel can not be used for building custom audiences because another pixel is already used: test."
                    },
                    "data": None,
                },
                "success": False,
            },
            json.loads(response.content),
        )

        self.assertFalse(ping_mock.called)
        self.assertFalse(redirector_mock.called)

        audience_enabled_pixels = models.ConversionPixel.objects.filter(audience_enabled=True).filter(account_id=1)
        self.assertEqual(1, len(audience_enabled_pixels))
        self.assertEqual(1, existing_audience_enabled_pixels[0].id)

    @patch("utils.redirector_helper.upsert_audience")
    def test_put_archive(self, redirector_mock):
        add_permissions(self.user, ["archive_restore_entity"])

        conversion_pixel = models.ConversionPixel.objects.get(pk=2)
        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 2}),
            json.dumps({"archived": True, "name": conversion_pixel.name, "audience_enabled": False}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertDictEqual(
            {
                "id": 2,
                "archived": True,
                "name": "test2",
                "url": settings.CONVERSION_PIXEL_PREFIX + "1/test2/",
                "audience_enabled": False,
                "additional_pixel": False,
            },
            decoded_response["data"],
        )

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_ARCHIVE_RESTORE, hist.action_type)
        self.assertEqual("Archived conversion pixel named test2.", hist.changes_text)

        self.assertFalse(redirector_mock.called)

    @patch("utils.redirector_helper.upsert_audience")
    def test_put_archive_audience_enabled(self, redirector_mock):
        add_permissions(self.user, ["archive_restore_entity"])

        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"archived": True, "name": conversion_pixel.name, "audience_enabled": True}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(400, response.status_code)

        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        self.assertFalse(conversion_pixel.archived)

        self.assertDictEqual(
            {
                "data": {
                    "error_code": "ValidationError",
                    "message": None,
                    "errors": {"audience_enabled": "Can not archive pixel used for building custom audiences."},
                    "data": None,
                },
                "success": False,
            },
            json.loads(response.content),
        )

        self.assertFalse(redirector_mock.called)

    @patch("utils.redirector_helper.upsert_audience")
    def test_put_archive_additional_pixel_enabled(self, redirector_mock):
        add_permissions(self.user, ["archive_restore_entity"])

        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        conversion_pixel.additional_pixel = True
        conversion_pixel.audience_enabled = False
        conversion_pixel.save()
        models.ConversionPixel.objects.create(
            None, conversion_pixel.account, skip_notification=True, name="Audience pixel", audience_enabled=True
        )

        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"archived": True, "name": conversion_pixel.name, "additional_pixel": True}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)

        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        self.assertFalse(conversion_pixel.archived)
        self.assertDictEqual(
            {
                "data": {
                    "error_code": "ValidationError",
                    "message": None,
                    "errors": {"audience_enabled": "Can not archive pixel used for building custom audiences."},
                    "data": None,
                },
                "success": False,
            },
            json.loads(response.content),
        )

        self.assertFalse(redirector_mock.called)

    @patch("utils.redirector_helper.upsert_audience")
    def test_put_archive_no_permissions(self, redirector_mock):
        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        conversion_pixel.audience_enabled = False
        conversion_pixel.save()
        self.assertFalse(conversion_pixel.archived)

        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"archived": True, "name": conversion_pixel.name}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertDictEqual(
            {
                "id": 1,
                "archived": False,
                "name": conversion_pixel.name,
                "url": settings.CONVERSION_PIXEL_PREFIX + "1/test/",
                "audience_enabled": False,
                "additional_pixel": False,
            },
            decoded_response["data"],
        )

        self.assertFalse(redirector_mock.called)

    def test_put_invalid_pixel(self):
        conversion_pixel = models.ConversionPixel.objects.latest("id")

        add_permissions(self.user, ["archive_restore_entity"])
        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": conversion_pixel.id + 1}),
            json.dumps({"archived": True}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(404, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual("Conversion pixel does not exist", decoded_response["data"]["message"])

    def test_put_invalid_account(self):
        account = models.Account.objects.get(id=4)
        new_conversion_pixel = models.ConversionPixel.objects.create(
            None, account=account, skip_notification=True, name="abcd"
        )

        add_permissions(self.user, ["archive_restore_entity"])
        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": new_conversion_pixel.id}),
            json.dumps({"archived": True}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(404, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual("Conversion pixel does not exist", decoded_response["data"]["message"])

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.redirector_helper.update_pixel")
    def test_put_redirect_url(self, update_pixel_mock, upsert_audience_mock):
        add_permissions(self.user, ["can_redirect_pixels"])
        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        conversion_pixel.audience_enabled = False
        conversion_pixel.save()
        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"name": "test", "audience_enabled": False, "redirect_url": "http://test.com"}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual(
            {
                "id": 1,
                "archived": conversion_pixel.archived,
                "name": "test",
                "url": settings.CONVERSION_PIXEL_PREFIX + "1/test/",
                "audience_enabled": False,
                "additional_pixel": False,
                "redirect_url": "http://test.com",
            },
            decoded_response["data"],
        )

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_SET_REDIRECT_URL, hist.action_type)
        self.assertEqual("Set redirect url of pixel named test to http://test.com.", hist.changes_text)

        self.assertEqual(upsert_audience_mock.call_count, 0)
        update_pixel_mock.assert_called_once_with(conversion_pixel)

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.redirector_helper.update_pixel")
    def test_put_redirect_url_remove(self, update_pixel_mock, upsert_audience_mock):
        add_permissions(self.user, ["can_redirect_pixels"])
        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        conversion_pixel.redirect_url = "http://test.com"
        conversion_pixel.audience_enabled = False
        conversion_pixel.save()

        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"name": "test", "audience_enabled": False, "redirect_url": ""}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual(
            {
                "id": 1,
                "archived": conversion_pixel.archived,
                "name": "test",
                "url": settings.CONVERSION_PIXEL_PREFIX + "1/test/",
                "audience_enabled": False,
                "additional_pixel": False,
                "redirect_url": "",
            },
            decoded_response["data"],
        )

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_SET_REDIRECT_URL, hist.action_type)
        self.assertEqual("Removed redirect url of pixel named test.", hist.changes_text)

        self.assertEqual(upsert_audience_mock.call_count, 0)
        update_pixel_mock.assert_called_once_with(conversion_pixel)

    def test_put_redirect_url_invalid(self):
        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"name": "test", "audience_enabled": False, "redirect_url": "invalidurl"}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(400, response.status_code)
        decoded_response = json.loads(response.content)

        self.assertEqual(["Enter a valid URL."], decoded_response["data"]["errors"]["redirect_url"])

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.redirector_helper.update_pixel")
    def test_put_notes(self, update_pixel_mock, upsert_audience_mock):

        add_permissions(self.user, ["can_see_pixel_notes"])
        conversion_pixel = models.ConversionPixel.objects.get(pk=1)
        conversion_pixel.audience_enabled = False
        conversion_pixel.save()
        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"name": "test", "audience_enabled": False, "notes": "test notes"}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(200, response.status_code)

        decoded_response = json.loads(response.content)
        self.assertEqual(
            {
                "id": 1,
                "archived": conversion_pixel.archived,
                "name": "test",
                "url": settings.CONVERSION_PIXEL_PREFIX + "1/test/",
                "audience_enabled": False,
                "additional_pixel": False,
                "notes": "test notes",
            },
            decoded_response["data"],
        )

        self.assertEqual(upsert_audience_mock.call_count, 0)
        self.assertEqual(update_pixel_mock.call_count, 0)

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.redirector_helper.update_pixel")
    def test_put_set_additional_pixel_no_permissions(self, update_pixel_mock, upsert_audience_mock):
        conversion_pixel = models.ConversionPixel.objects.get(id=1)
        self.assertFalse(conversion_pixel.additional_pixel)
        conversion_pixel.audience_enabled = False
        conversion_pixel.save()
        self.assertFalse(conversion_pixel.audience_enabled)

        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"additional_pixel": True, "name": conversion_pixel.name}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)["data"]
        self.assertFalse(data["additional_pixel"])

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertFalse(hist)

        self.assertEqual(upsert_audience_mock.call_count, 0)
        self.assertEqual(update_pixel_mock.call_count, 0)

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.redirector_helper.update_pixel")
    def test_put_set_additional_pixel(self, update_pixel_mock, upsert_audience_mock):
        add_permissions(self.user, ["can_promote_additional_pixel"])
        conversion_pixel = models.ConversionPixel.objects.get(id=1)
        conversion_pixel.audience_enabled = False
        conversion_pixel.save()
        models.ConversionPixel.objects.create(
            None, conversion_pixel.account, skip_notification=True, name="Audience pixel", audience_enabled=True
        )

        self.assertFalse(conversion_pixel.audience_enabled)
        self.assertFalse(conversion_pixel.additional_pixel)

        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"additional_pixel": True, "name": conversion_pixel.name}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)["data"]
        self.assertTrue(data["additional_pixel"])
        conversion_pixel = models.ConversionPixel.objects.get(id=1)
        self.assertTrue(conversion_pixel.additional_pixel)

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_SET_ADDITIONAL_PIXEL, hist.action_type)
        self.assertEqual(
            "Set pixel {} as an additional audience pixel.".format(conversion_pixel.name), hist.changes_text
        )

        self.assertEqual(upsert_audience_mock.call_count, 4)
        self.assertEqual(update_pixel_mock.call_count, 1)

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.redirector_helper.update_pixel")
    def test_put_unset_additional_pixel_no_change(self, update_pixel_mock, upsert_audience_mock):
        add_permissions(self.user, ["can_promote_additional_pixel"])
        conversion_pixel = models.ConversionPixel.objects.get(id=1)
        conversion_pixel.additional_pixel = True
        conversion_pixel.save()
        upsert_audience_mock.reset_mock()
        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"additional_pixel": False, "name": conversion_pixel.name}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)["data"]
        self.assertTrue(data["additional_pixel"])
        conversion_pixel = models.ConversionPixel.objects.get(id=1)
        self.assertTrue(conversion_pixel.additional_pixel)

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertFalse(hist)

        self.assertFalse(update_pixel_mock.called)
        self.assertFalse(upsert_audience_mock.called)

    @patch("utils.k1_helper.update_account")
    def test_post_additional_pixel_enabled(self, ping_mock):
        add_permissions(self.user, ["can_promote_additional_pixel"])
        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name", "additional_pixel": True}),
            content_type="application/json",
            follow=True,
        )

        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)["data"]
        self.assertTrue(data["additional_pixel"])
        pixel_created = models.ConversionPixel.objects.filter(name="name", additional_pixel=True).count()
        self.assertEqual(1, pixel_created)

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.CONVERSION_PIXEL_CREATE_AS_ADDITIONAL, hist.action_type)
        self.assertEqual("Created a conversion pixel named name as an additional audience pixel.", hist.changes_text)

        ping_mock.assert_called_once_with(models.Account.objects.get(pk=1), msg="conversion_pixel.create")

    @patch("utils.k1_helper.update_account")
    def test_post_additional_pixel_enabled_without_permissions(self, ping_mock):
        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name", "additional_pixel": True}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)["data"]
        self.assertEqual(
            {
                "id": data["id"],
                "name": "name",
                "url": settings.CONVERSION_PIXEL_PREFIX + "1/{}/".format(data["id"]),
                "archived": False,
                "audience_enabled": False,
                "additional_pixel": False,
            },
            data,
        )
        pixel_created = models.ConversionPixel.objects.filter(name="name", additional_pixel=True).count()
        self.assertEqual(0, pixel_created)

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertTrue(hist)

        self.assertFalse(ping_mock.called)

    @patch("utils.k1_helper.update_account")
    def test_post_additional_pixel_without_existing_audience_pixel(self, ping_mock):
        audience_enabled_pixel = models.ConversionPixel.objects.get(id=1)
        audience_enabled_pixel.audience_enabled = False
        audience_enabled_pixel.save()
        audience_disabled = models.ConversionPixel.objects.filter(audience_enabled=True).filter(account_id=1).count()
        self.assertEqual(0, audience_disabled)

        add_permissions(self.user, ["can_promote_additional_pixel"])
        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name", "additional_pixel": True}),
            content_type="application/json",
            follow=True,
        )
        data = json.loads(response.content)["data"]["errors"]

        self.assertEqual(400, response.status_code)
        self.assertEqual(
            {
                "additional_pixel": (
                    [
                        "The pixel's account has no audience pixel set. Set an audience pixel"
                        " before setting an additional audience pixel."
                    ]
                )
            },
            data,
        )
        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertFalse(hist)

        self.assertFalse(ping_mock.called)

    @patch("utils.redirector_helper.upsert_audience")
    @patch("utils.redirector_helper.update_pixel")
    def test_put_set_additional_pixel_on_audience_pixel(self, update_pixel_mock, upsert_audience_mock):
        add_permissions(self.user, ["can_promote_additional_pixel"])
        conversion_pixel = models.ConversionPixel.objects.get(id=1)
        self.assertTrue(conversion_pixel.audience_enabled)

        response = self.client.put(
            reverse("conversion_pixel", kwargs={"conversion_pixel_id": 1}),
            json.dumps({"name": "name", "audience_enabled": True, "additional_pixel": True}),
            content_type="application/json",
            follow=True,
        )
        error = json.loads(response.content)["data"]["errors"]
        self.assertTrue(response.status_code)
        self.assertDictEqual(
            {
                "additional_pixel": (
                    ["Custom audience and additional audience can not be enabled at the same time on the same pixel."]
                )
            },
            error,
        )

        no_pixel_found = models.ConversionPixel.objects.filter(
            account=1, name="name", audience_enabled=True, additional_pixel=True
        ).all()
        self.assertFalse(no_pixel_found)

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertFalse(hist)

        self.assertFalse(upsert_audience_mock.called)
        self.assertEqual(update_pixel_mock.call_count, 0)

    @patch("utils.k1_helper.update_account")
    def test_post_set_additional_pixel_on_audience_pixel(self, ping_mock):
        add_permissions(self.user, ["can_promote_additional_pixel"])

        response = self.client.post(
            reverse("account_conversion_pixels", kwargs={"account_id": 1}),
            json.dumps({"name": "name", "audience_enabled": True, "additional_pixel": True}),
            content_type="application/json",
            follow=True,
        )
        error = json.loads(response.content)["data"]["errors"]

        self.assertTrue(response.status_code)
        self.assertDictEqual(
            {
                "additional_pixel": (
                    ["Custom audience and additional audience can not be enabled at the same time on the same pixel."]
                )
            },
            error,
        )
        no_pixel_found = models.ConversionPixel.objects.filter(
            account=1, name="name", audience_enabled=True, additional_pixel=True
        ).all()
        self.assertFalse(no_pixel_found)

        hist = history_helpers.get_account_history(models.Account.objects.get(pk=1)).first()
        self.assertFalse(hist)

        self.assertFalse(ping_mock.called)


class UserActivationTest(TestCase):
    fixtures = ["test_views.yaml", "test_non_superuser.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=1)

        self.assertFalse(self.user.is_superuser)

        self.client.login(username=self.user.email, password="secret")

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = datetime.datetime(2015, 6, 5, 13, 22, 20)

    def test_permissions(self):
        url = reverse("account_user_action", kwargs={"account_id": 0, "user_id": 0, "action": "activate"})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    def test_send_mail(self):
        request = HttpRequest()
        request.user = User(id=1)

        data = {}

        add_permissions(self.user, ["account_agency_access_permissions"])
        response = self.client.post(
            reverse("account_user_action", kwargs={"account_id": 1, "user_id": 1, "action": "activate"}),
            data,
            follow=True,
        )

        decoded_response = json.loads(response.content)
        self.assertTrue(decoded_response.get("success"))

        self.assertGreater(len(mail.outbox), 0, "Successfully sent mail.")

        sent_mail = mail.outbox[0]
        self.assertEqual("Welcome to Zemanta!", sent_mail.subject, "Title must match activation mail")
        self.assertTrue(self.user.email in sent_mail.recipients())

    @patch("utils.email_helper.send_email_to_new_user")  # , mock=Mock(side_effect=User.DoesNotExist))
    def test_send_mail_failure(self, mock):
        request = HttpRequest()
        request.user = User(id=1)

        mock.side_effect = User.DoesNotExist

        data = {}

        add_permissions(self.user, ["account_agency_access_permissions"])
        response = self.client.post(
            reverse("account_user_action", kwargs={"account_id": 1, "user_id": 1, "action": "activate"}),
            data,
            follow=True,
        )

        decoded_response = json.loads(response.content)
        self.assertFalse(decoded_response.get("success"), "Failed sending message")


class AccountUsersTest(TestCase):
    fixtures = ["test_views.yaml", "test_agency.yaml"]

    def _get_client_with_permissions(self, permissions_list):
        password = "secret"
        user = User.objects.get(pk=2)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client

    def test_get(self):
        client = self._get_client_with_permissions(["account_agency_access_permissions"])
        response = client.get(reverse("account_users", kwargs={"account_id": 1}))
        user = User.objects.get(pk=2)

        self.assertIsNone(response.json()["data"]["agency_managers"])
        self.assertCountEqual(
            [
                {
                    "name": "",
                    "is_active": True,
                    "is_agency_manager": False,
                    "id": 2,
                    "last_login": user.last_login.date().isoformat(),
                    "email": "user@test.com",
                    "can_use_restapi": False,
                },
                {
                    "name": "",
                    "is_active": False,
                    "is_agency_manager": False,
                    "id": 3,
                    "last_login": "2014-06-16",
                    "email": "john@test.com",
                    "can_use_restapi": False,
                },
                {
                    "name": "",
                    "is_active": False,
                    "is_agency_manager": False,
                    "id": 1,
                    "last_login": "2014-06-16",
                    "email": "superuser@test.com",
                    "can_use_restapi": True,
                },
            ],
            response.json()["data"]["users"],
        )

    def test_get_agency(self):
        client = self._get_client_with_permissions(["account_agency_access_permissions"])

        acc = models.Account.objects.get(pk=1)
        agency = models.Agency.objects.get(pk=1)
        acc.agency = agency
        acc.save(fake_request(User.objects.get(pk=1)))

        user = User.objects.get(pk=1)
        agency.users.add(User.objects.get(pk=1))

        user = User.objects.get(pk=2)
        response = client.get(reverse("account_users", kwargs={"account_id": 1}))

        self.assertCountEqual(
            [
                {
                    "name": "",
                    "is_active": False,
                    "is_agency_manager": True,
                    "id": 1,
                    "last_login": "2014-06-16",
                    "email": "superuser@test.com",
                    "can_use_restapi": True,
                }
            ],
            response.json()["data"]["agency_managers"],
        )

        self.assertCountEqual(
            [
                {
                    "name": "",
                    "is_active": True,
                    "is_agency_manager": False,
                    "id": 2,
                    "last_login": user.last_login.date().isoformat(),
                    "email": "user@test.com",
                    "can_use_restapi": False,
                },
                {
                    "name": "",
                    "is_active": False,
                    "is_agency_manager": False,
                    "id": 3,
                    "last_login": "2014-06-16",
                    "email": "john@test.com",
                    "can_use_restapi": False,
                },
                {
                    "name": "",
                    "is_active": False,
                    "is_agency_manager": False,
                    "id": 1,
                    "last_login": "2014-06-16",
                    "email": "superuser@test.com",
                    "can_use_restapi": True,
                },
            ],
            response.json()["data"]["users"],
        )

    def test_get_agency_with_can_see_agency_managers(self):
        client = self._get_client_with_permissions(
            ["account_agency_access_permissions", "can_see_agency_managers_under_access_permissions"]
        )

        acc = models.Account.objects.get(pk=1)
        agency = models.Agency.objects.get(pk=1)
        acc.agency = agency
        acc.save(fake_request(User.objects.get(pk=1)))

        user = User.objects.get(pk=1)
        agency.users.add(User.objects.get(pk=1))

        user = User.objects.get(pk=2)
        response = client.get(reverse("account_users", kwargs={"account_id": 1}))

        self.assertCountEqual(
            [
                {
                    "name": "",
                    "is_active": False,
                    "is_agency_manager": True,
                    "id": 1,
                    "last_login": "2014-06-16",
                    "email": "superuser@test.com",
                    "can_use_restapi": True,
                }
            ],
            response.json()["data"]["agency_managers"],
        )

        self.assertCountEqual(
            [
                {
                    "name": "",
                    "is_active": False,
                    "is_agency_manager": True,
                    "id": 1,
                    "last_login": "2014-06-16",
                    "email": "superuser@test.com",
                    "can_use_restapi": True,
                },
                {
                    "name": "",
                    "is_active": True,
                    "is_agency_manager": False,
                    "id": 2,
                    "last_login": user.last_login.date().isoformat(),
                    "email": "user@test.com",
                    "can_use_restapi": False,
                },
                {
                    "name": "",
                    "is_active": False,
                    "is_agency_manager": False,
                    "id": 3,
                    "last_login": "2014-06-16",
                    "email": "john@test.com",
                    "can_use_restapi": False,
                },
                {
                    "name": "",
                    "is_active": False,
                    "is_agency_manager": False,
                    "id": 1,
                    "last_login": "2014-06-16",
                    "email": "superuser@test.com",
                    "can_use_restapi": True,
                },
            ],
            response.json()["data"]["users"],
        )

    def test_remove_normal_user(self):
        client = self._get_client_with_permissions(["account_agency_access_permissions"])

        acc1 = models.Account.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)

        agency = models.Agency.objects.get(pk=1)
        acc1.agency = agency
        acc1.save(fake_request(User.objects.get(pk=1)))
        acc2.agency = agency
        acc2.save(fake_request(User.objects.get(pk=1)))

        agency.users.add(User.objects.get(pk=1))

        user = User.objects.get(pk=2)
        acc1.users.add(user)
        acc2.users.add(user)
        response = client.delete(reverse("account_users_manage", kwargs={"account_id": 1, "user_id": user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(acc1.users.filter(pk=user.pk))
        self.assertTrue(acc2.users.filter(pk=user.pk))

    def test_remove_normal_user_from_all_accounts(self):
        client = self._get_client_with_permissions(["account_agency_access_permissions"])

        acc1 = models.Account.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)

        agency = models.Agency.objects.get(pk=1)
        acc1.agency = agency
        acc1.save(fake_request(User.objects.get(pk=1)))
        acc2.agency = agency
        acc2.save(fake_request(User.objects.get(pk=1)))

        agency.users.add(User.objects.get(pk=1))

        permission = authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)

        user = User.objects.get(pk=2)
        acc1.users.add(user)
        acc2.users.add(user)
        response = client.delete(
            reverse("account_users_manage", kwargs={"account_id": 1, "user_id": user.pk})
            + "?remove_from_all_accounts=1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(acc1.users.filter(pk=user.pk))
        self.assertFalse(acc2.users.filter(pk=user.pk))

    def test_remove_agency_user(self):
        client = self._get_client_with_permissions(["account_agency_access_permissions"])

        acc1 = models.Account.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)

        agency = models.Agency.objects.get(pk=1)
        acc1.agency = agency
        acc1.save(fake_request(User.objects.get(pk=1)))
        acc2.agency = agency
        acc2.save(fake_request(User.objects.get(pk=1)))

        agency.users.add(User.objects.get(pk=1))

        permission = authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)

        user = User.objects.get(pk=2)
        user.first_name = "Someone"
        user.last_name = "Important"
        user.save()

        acc1.users.add(user)
        acc2.users.add(user)
        agency.users.add(user)

        response = client.delete(reverse("account_users_manage", kwargs={"account_id": 1, "user_id": user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(acc1.users.filter(pk=user.pk))
        self.assertFalse(acc2.users.filter(pk=user.pk))
        self.assertFalse(agency.users.filter(pk=user.pk))
        self.assertEqual(
            models.History.objects.filter(agency=agency, account=None).order_by("-created_dt").first().changes_text,
            "Removed agency user Someone Important (user@test.com)",
        )

    def test_remove_multiagency_user(self):
        client = self._get_client_with_permissions(["account_agency_access_permissions"])

        acc1 = models.Account.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)
        acc3 = magic_mixer.blend(models.Account)
        acc4 = magic_mixer.blend(models.Account)

        agency = models.Agency.objects.get(pk=1)
        acc1.agency = agency
        acc1.save(fake_request(User.objects.get(pk=1)))
        acc2.agency = agency
        acc2.save(fake_request(User.objects.get(pk=1)))
        agency.users.add(User.objects.get(pk=1))

        agency2 = magic_mixer.blend(models.Agency)
        acc3.agency = agency2
        acc3.save(fake_request(User.objects.get(pk=1)))
        acc4.agency = agency2
        acc4.save(fake_request(User.objects.get(pk=1)))
        agency.users.add(User.objects.get(pk=1))

        permission = authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)

        user = User.objects.get(pk=2)
        user.first_name = "Someone"
        user.last_name = "Important"
        user.save()

        acc1.users.add(user)
        acc2.users.add(user)
        acc3.users.add(user)
        acc4.users.add(user)
        agency.users.add(user)
        agency2.users.add(user)

        response = client.delete(reverse("account_users_manage", kwargs={"account_id": 1, "user_id": user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(acc1.users.filter(pk=user.pk))
        self.assertFalse(acc2.users.filter(pk=user.pk))
        self.assertFalse(agency.users.filter(pk=user.pk))
        self.assertTrue(agency2.users.filter(pk=user.pk))
        self.assertTrue(acc3.users.filter(pk=user.pk))
        self.assertTrue(acc4.users.filter(pk=user.pk))
        self.assertIn(permission, group.permissions.all())
        self.assertEqual(
            models.History.objects.filter(agency=agency, account=None).order_by("-created_dt").first().changes_text,
            "Removed agency user Someone Important (user@test.com)",
        )

    def test_remove_multiagency_user_from_all_account(self):
        client = self._get_client_with_permissions(["account_agency_access_permissions"])

        acc1 = models.Account.objects.get(pk=1)
        acc2 = models.Account.objects.get(pk=2)
        acc3 = magic_mixer.blend(models.Account)
        acc4 = magic_mixer.blend(models.Account)

        agency = models.Agency.objects.get(pk=1)
        acc1.agency = agency
        acc1.save(fake_request(User.objects.get(pk=1)))
        acc2.agency = agency
        acc2.save(fake_request(User.objects.get(pk=1)))
        agency.users.add(User.objects.get(pk=1))

        agency2 = magic_mixer.blend(models.Agency)
        acc3.agency = agency2
        acc3.save(fake_request(User.objects.get(pk=1)))
        acc4.agency = agency2
        acc4.save(fake_request(User.objects.get(pk=1)))
        agency.users.add(User.objects.get(pk=1))

        permission = authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)

        user = User.objects.get(pk=2)
        user.first_name = "Someone"
        user.last_name = "Important"
        user.save()

        acc1.users.add(user)
        acc2.users.add(user)
        acc3.users.add(user)
        acc4.users.add(user)
        agency.users.add(user)
        agency2.users.add(user)

        response = client.delete(
            reverse("account_users_manage", kwargs={"account_id": 1, "user_id": user.pk})
            + "?remove_from_all_accounts=1"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(acc1.users.filter(pk=user.pk))
        self.assertFalse(acc2.users.filter(pk=user.pk))
        self.assertFalse(agency.users.filter(pk=user.pk))
        self.assertTrue(agency2.users.filter(pk=user.pk))
        self.assertTrue(acc3.users.filter(pk=user.pk))
        self.assertTrue(acc4.users.filter(pk=user.pk))
        self.assertIn(permission, group.permissions.all())
        self.assertEqual(
            models.History.objects.filter(agency=agency, account=None).order_by("-created_dt").first().changes_text,
            "Removed agency user Someone Important (user@test.com)",
        )


class UserPromoteTest(TestCase):
    fixtures = ["test_views.yaml", "test_agency.yaml"]

    def _get_client_with_permissions(self, permissions_list):
        password = "secret"
        user = User.objects.get(pk=2)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client

    def test_without_permission(self):
        client = self._get_client_with_permissions([])

        response = client.post(
            reverse("account_user_action", kwargs={"account_id": 1000, "user_id": 2, "action": "promote"})
        )

        self.assertEqual(401, response.status_code)

    def test_promote(self):
        client = self._get_client_with_permissions(["can_promote_agency_managers"])

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)
        permission = authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)
        account.users.add(user)

        response = client.post(
            reverse("account_user_action", kwargs={"account_id": 1000, "user_id": 2, "action": "promote"})
        )
        self.assertEqual(200, response.status_code)

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)

        self.assertIn(user, agency.users.all())
        self.assertNotIn(user, account.users.all())
        self.assertIn(group, user.groups.all())

    def test_promote_unrelated_user(self):
        client = self._get_client_with_permissions(["can_promote_agency_managers"])

        account = models.Account.objects.get(pk=1000)
        user = User.objects.get(pk=2)
        permission = authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)
        account.users.add(user)

        user2 = User.objects.get(pk=3)
        account.users.remove(user2)

        response = client.post(
            reverse("account_user_action", kwargs={"account_id": 1000, "user_id": 3, "action": "promote"})
        )
        self.assertEqual(401, response.status_code)
        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=3)
        self.assertNotIn(user, agency.users.all())
        self.assertNotIn(user, account.users.all())


class UserDowngradeTest(TestCase):
    fixtures = ["test_views.yaml", "test_agency.yaml"]

    def _get_client_with_permissions(self, permissions_list):
        password = "secret"
        user = User.objects.get(pk=2)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client

    def test_without_permission(self):
        client = self._get_client_with_permissions([])

        response = client.post(
            reverse("account_user_action", kwargs={"account_id": 1000, "user_id": 2, "action": "downgrade"})
        )

        self.assertEqual(401, response.status_code)

    def test_downgrade(self):
        client = self._get_client_with_permissions(["can_promote_agency_managers"])

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)
        permission = authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)
        agency.users.add(user)
        user.groups.add(group)

        response = client.post(
            reverse("account_user_action", kwargs={"account_id": 1000, "user_id": 2, "action": "downgrade"})
        )
        self.assertEqual(200, response.status_code)

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)

        self.assertNotIn(user, agency.users.all())
        self.assertIn(user, account.users.all())
        self.assertNotIn(group, user.groups.all())

    def test_downgrade_unrelated_user(self):
        client = self._get_client_with_permissions(["can_promote_agency_managers"])

        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=2)
        permission = authmodels.Permission.objects.get(codename="this_is_agency_manager_group")
        group = authmodels.Group()
        group.save()
        group.permissions.add(permission)
        agency.users.add(user)

        user2 = User.objects.get(pk=3)
        account.users.remove(user2)

        response = client.post(
            reverse("account_user_action", kwargs={"account_id": 1000, "user_id": 3, "action": "downgrade"})
        )
        self.assertEqual(401, response.status_code)
        account = models.Account.objects.get(pk=1000)
        agency = models.Agency.objects.get(pk=1)
        user = User.objects.get(pk=3)
        self.assertNotIn(user, agency.users.all())
        self.assertNotIn(user, account.users.all())


class UserEnableRESTAPIAccessTest(TestCase):
    fixtures = ["test_views.yaml", "test_agency.yaml"]

    def _get_client_with_permissions(self, permissions_list):
        password = "secret"
        user = User.objects.get(pk=2)
        add_permissions(user, permissions_list)
        user.save()
        client = Client()
        client.login(username=user.email, password=password)
        return client

    def test_without_permission(self):
        client = self._get_client_with_permissions([])
        response = client.post(
            reverse("account_user_action", kwargs={"account_id": 1000, "user_id": 2, "action": "enable_api"})
        )
        self.assertEqual(401, response.status_code)

    @patch("utils.email_helper.send_official_email")
    def test_enable_api(self, mocking_email):
        client = self._get_client_with_permissions(["can_manage_restapi_access"])
        client_user = User.objects.get(pk=2)
        user = User.objects.get(pk=3)
        user.first_name = "TestUser First Name"
        user.save()
        account = models.Account.objects.get(pk=1000)
        account.users.add(user)
        account.users.add(client_user)
        perm = Permission.objects.get(codename="can_use_restapi")
        perm_indicator = Permission.objects.get(codename="this_is_restapi_group")
        group = authmodels.Group.objects.create(name="api_access_group")
        group.permissions.add(perm)
        group.permissions.add(perm_indicator)
        self.assertFalse(user.has_perm("zemauth.can_use_restapi"))

        response = client.post(
            reverse("account_user_action", kwargs={"account_id": 1000, "user_id": 3, "action": "enable_api"})
        )
        user = User.objects.get(pk=3)

        self.assertEqual(200, response.status_code)
        self.assertIn(user, authmodels.Group.objects.get(permissions=perm).user_set.all())
        self.assertTrue(user.has_perm("zemauth.can_use_restapi"))
        self.assertTrue(mocking_email.called)
        args = {
            "agency_or_user": user,
            "subject": "User was granted REST API access",
            "body": """
Hello TestUser First Name,

You are now able to use the <a href="http://dev.zemanta.com/one/api/">Zemanta REST API</a>.
As mentioned in our <a href="http://dev.zemanta.com/one/api/">documentation</a>, the first step is to register
your application. Click on this <a href="https://one.zemanta.com/o/applications/register/">link</a> to do it now!

Make good use of it!

Yours truly,
Zemanta""",
            "additional_recipients": [],
            "tags": ["USER_ENABLE_RESTAPI"],
            "recipient_list": ["john@test.com"],
        }
        mocking_email.assert_called_once_with(**args)


class CampaignContentInsightsTest(TestCase):
    fixtures = ["test_views.yaml"]

    def user(self):
        return User.objects.get(pk=2)

    @patch("redshiftapi.api_breakdowns.query")
    def test_permission(self, mock_query):
        cis = agency.CampaignContentInsights()
        with self.assertRaises(exc.AuthorizationError):
            cis.get(fake_request(self.user()), 1)

        add_permissions(self.user(), ["can_view_campaign_content_insights_side_tab"])
        request = fake_request(self.user())
        request.GET = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
        response = cis.get(request, 1)
        self.assertEqual(http.client.OK, response.status_code)
        self.assertDictEqual(
            {
                "data": {"metric": "CTR", "summary": "Title", "best_performer_rows": [], "worst_performer_rows": []},
                "success": True,
            },
            json.loads(response.content),
        )

    @patch("redshiftapi.api_breakdowns.query")
    def test_basic_archived(self, mock_query):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ["can_view_campaign_content_insights_side_tab"])

        campaign = models.Campaign.objects.get(pk=1)
        cad = models.ContentAd(
            ad_group=campaign.adgroup_set.first(),
            title="Test Ad",
            url="http://www.zemanta.com",
            batch_id=1,
            archived=True,
        )
        cad.save()

        mock_query.return_value = [{"content_ad_id": cad.id, "clicks": 1000, "impressions": 10000}]
        request = fake_request(self.user())
        request.GET = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
        response = cis.get(request, 1)
        self.assertEqual(http.client.OK, response.status_code)
        self.assertDictEqual(
            {
                "data": {"metric": "CTR", "summary": "Title", "best_performer_rows": [], "worst_performer_rows": []},
                "success": True,
            },
            json.loads(response.content),
        )

    @patch("redshiftapi.api_breakdowns.query")
    def test_basic_title_ctr(self, mock_query):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ["can_view_campaign_content_insights_side_tab"])

        campaign = models.Campaign.objects.get(pk=1)
        cad = models.ContentAd(
            ad_group=campaign.adgroup_set.first(), title="Test Ad", url="http://www.zemanta.com", batch_id=1
        )
        cad.save()

        mock_query.return_value = [{"content_ad_id": cad.id, "clicks": 1000, "impressions": 10000}]

        request = fake_request(self.user())
        request.GET = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
        response = cis.get(request, 1)
        self.assertEqual(http.client.OK, response.status_code)
        self.assertDictEqual(
            {
                "data": {
                    "metric": "CTR",
                    "summary": "Title",
                    "best_performer_rows": [{"summary": "Test Ad", "metric": "10.00%"}],
                    "worst_performer_rows": [{"summary": "Test Ad", "metric": "10.00%"}],
                },
                "success": True,
            },
            json.loads(response.content),
        )

    @patch("redshiftapi.api_breakdowns.query")
    def test_duplicate_title_ctr(self, mock_query):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ["can_view_campaign_content_insights_side_tab"])

        campaign = models.Campaign.objects.get(pk=1)
        cad1 = models.ContentAd(
            ad_group=campaign.adgroup_set.first(), title="Test Ad", url="http://www.zemanta.com", batch_id=1
        )
        cad1.save()

        cad2 = models.ContentAd(
            ad_group=campaign.adgroup_set.first(), title="Test Ad", url="http://www.bidder.com", batch_id=1
        )
        cad2.save()

        mock_query.return_value = [
            {"content_ad_id": cad1.id, "clicks": 1000, "impressions": 10000},
            {"content_ad_id": cad2.id, "clicks": 9000, "impressions": 10000},
        ]

        request = fake_request(self.user())
        request.GET = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
        response = cis.get(request, 1)
        self.assertEqual(http.client.OK, response.status_code)
        self.assertDictEqual(
            {
                "data": {
                    "metric": "CTR",
                    "summary": "Title",
                    "best_performer_rows": [{"summary": "Test Ad", "metric": "50.00%"}],
                    "worst_performer_rows": [{"summary": "Test Ad", "metric": "50.00%"}],
                },
                "success": True,
            },
            json.loads(response.content),
        )

    @patch("redshiftapi.api_breakdowns.query")
    def test_order_title_ctr(self, mock_query):
        cis = agency.CampaignContentInsights()
        add_permissions(self.user(), ["can_view_campaign_content_insights_side_tab"])

        campaign = models.Campaign.objects.get(pk=1)
        cad1 = models.ContentAd(
            ad_group=campaign.adgroup_set.first(), title="Test Ad", url="http://www.zemanta.com", batch_id=1
        )
        cad1.save()

        cad2 = models.ContentAd(
            ad_group=campaign.adgroup_set.first(), title="Awesome Ad", url="http://www.bidder.com", batch_id=1
        )
        cad2.save()

        mock_query.return_value = [
            {"content_ad_id": cad1.id, "clicks": 100, "impressions": 100000},
            {"content_ad_id": cad2.id, "clicks": 1000, "impressions": 100000},
        ]

        request = fake_request(self.user())
        request.GET = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
        response = cis.get(request, 1)
        self.assertEqual(http.client.OK, response.status_code)
        self.assertDictEqual(
            {
                "data": {
                    "metric": "CTR",
                    "summary": "Title",
                    "best_performer_rows": [
                        {"metric": "1.00%", "summary": "Awesome Ad"},
                        {"metric": "0.10%", "summary": "Test Ad"},
                    ],
                    "worst_performer_rows": [
                        {"metric": "0.10%", "summary": "Test Ad"},
                        {"metric": "1.00%", "summary": "Awesome Ad"},
                    ],
                },
                "success": True,
            },
            json.loads(response.content),
        )


class HistoryTest(TestCase):
    fixtures = ["test_api.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=2)

    def _add_entries(self):
        self.dt = datetime.datetime.utcnow()
        ad_group = models.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        account = campaign.account

        models.History.objects.create(
            ad_group=ad_group,
            campaign=campaign,
            account=account,
            level=constants.HistoryLevel.AD_GROUP,
            changes={"name": "test"},
            changes_text="Name changed to 'test'",
            created_by=self.user,
        )

        models.History.objects.create(
            campaign=campaign,
            account=account,
            level=constants.HistoryLevel.CAMPAIGN,
            changes={"targeting": ["US"]},
            changes_text="Geographic targeting changed to 'US'",
            created_dt=self.dt,
            created_by=self.user,
        )
        models.History.objects.create(
            account=account,
            level=constants.HistoryLevel.ACCOUNT,
            changes={"account_manager": 1},
            changes_text="Account manager changed to 'Janez Novak'",
            created_dt=self.dt,
            created_by=self.user,
        )

    def get_history(self, filters):
        self.client.login(username=self.user.username, password="secret")
        reversed_url = reverse("history", kwargs={})
        response = self.client.get(reversed_url, filters, follow=True)
        return response.json()

    def test_permission(self):
        response = self.get_history({})
        self.assertFalse(response["success"])

        add_permissions(self.user, ["can_view_new_history_backend"])
        response = self.get_history({})
        self.assertFalse(response["success"])

        response = self.get_history({"campaign": 1})
        self.assertTrue(response["success"])

        response = self.get_history({"level": 0})
        self.assertFalse(response["success"])

    def test_get_ad_group_history(self):
        add_permissions(self.user, ["can_view_new_history_backend"])

        history_count = models.History.objects.all().count()
        self.assertEqual(0, history_count)

        self._add_entries()

        response = self.get_history({"ad_group": 1})
        self.assertTrue(response["success"])
        self.assertEqual(1, len(response["data"]["history"]))

        history = response["data"]["history"][0]
        self.assertEqual(self.user.email, history["changed_by"])
        self.assertEqual("Name changed to 'test'", history["changes_text"])

    def test_get_campaign_history(self):
        add_permissions(self.user, ["can_view_new_history_backend"])

        history_count = models.History.objects.all().count()
        self.assertEqual(0, history_count)

        self._add_entries()

        response = self.get_history({"campaign": 1, "level": constants.HistoryLevel.CAMPAIGN})
        self.assertTrue(response["success"])
        self.assertEqual(1, len(response["data"]["history"]))

        history = response["data"]["history"][0]
        self.assertEqual(self.user.email, history["changed_by"])
        self.assertEqual("Geographic targeting changed to 'US'", history["changes_text"])

        response = self.get_history({"campaign": 1})
        self.assertTrue(response["success"])
        self.assertEqual(2, len(response["data"]["history"]))

        history = response["data"]["history"][0]
        self.assertEqual(self.user.email, history["changed_by"])
        self.assertEqual("Geographic targeting changed to 'US'", history["changes_text"])

        history = response["data"]["history"][1]
        self.assertEqual(self.user.email, history["changed_by"])
        self.assertEqual("Name changed to 'test'", history["changes_text"])

    def test_get_account_history(self):
        add_permissions(self.user, ["can_view_new_history_backend"])

        history_count = models.History.objects.all().count()
        self.assertEqual(0, history_count)

        self._add_entries()

        response = self.get_history({"account": 1, "level": constants.HistoryLevel.ACCOUNT})
        self.assertTrue(response["success"])
        self.assertEqual(1, len(response["data"]["history"]))

        history = response["data"]["history"][0]
        self.assertEqual(self.user.email, history["changed_by"])
        self.assertEqual("Account manager changed to 'Janez Novak'", history["changes_text"])


class AgenciesTest(TestCase):
    fixtures = ["test_api.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.assertFalse(self.user.is_superuser)

    def get_agencies(self):
        self.client.login(username=self.user.username, password="secret")
        reversed_url = reverse("agencies", kwargs={})
        response = self.client.get(reversed_url, follow=True)
        return response.json()

    def test_permission(self):
        response = self.get_agencies()
        self.assertFalse(response["success"])

        add_permissions(self.user, ["can_filter_by_agency"])
        response = self.get_agencies()
        self.assertTrue(response["success"])

    def test_get(self):
        agency = models.Agency(name="test")
        agency.save(fake_request(self.user))

        add_permissions(self.user, ["can_filter_by_agency"])
        response = self.get_agencies()
        self.assertTrue(response["success"])
        self.assertEqual({"agencies": []}, response["data"])

        agency.users.add(self.user)
        agency.save(fake_request(self.user))

        response = self.get_agencies()
        self.assertTrue(response["success"])
        self.assertEqual(
            {"agencies": [{"id": str(agency.id), "name": "test", "is_externally_managed": False}]}, response["data"]
        )


class TestHistoryMixin(TestCase):
    class FakeMeta(object):
        def __init__(self, concrete_fields, virtual_fields):
            self.concrete_fields = concrete_fields
            self.virtual_fields = virtual_fields
            self.many_to_many = []

    class HistoryTest(history.HistoryMixinOld):

        history_fields = ["test_field"]

        def __init__(self):
            self._meta = TestHistoryMixin.FakeMeta(self.history_fields, [])
            self.id = None
            self.test_field = ""
            super(TestHistoryMixin.HistoryTest, self).__init__()

        def get_human_prop_name(self, prop):
            return "Test Field"

        def get_human_value(self, key, value):
            return value

        def get_defaults_dict(self):
            return {}

    def test_snapshot(self):
        mix = TestHistoryMixin.HistoryTest()
        mix.snapshot()
        self.assertEqual({"test_field": ""}, mix.snapshotted_state)
        self.assertTrue(mix.post_init_newly_created)

        mix.id = 5
        mix.snapshot(previous=mix)

        self.assertEqual({"test_field": ""}, mix.snapshotted_state)
        self.assertFalse(mix.post_init_newly_created)

    def test_get_history_dict(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual({"test_field": ""}, mix.get_history_dict())

    def test_get_model_state_changes(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual({}, mix.get_model_state_changes({"test_field": ""}))
        self.assertEqual({"test_field": "johnny"}, mix.get_model_state_changes({"test_field": "johnny"}))

    def test_get_history_changes_text(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual('Test Field set to "johnny"', mix.get_history_changes_text({"test_field": "johnny"}))

        self.assertEqual("", mix.get_history_changes_text({}))

    def test_get_changes_text_from_dict(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual(
            'Created settings. Test Field set to "johnny"', mix.get_changes_text_from_dict({"test_field": "johnny"})
        )

        self.assertEqual("Created settings", mix.get_changes_text_from_dict({}))

    def test_construct_changes(self):
        mix = TestHistoryMixin.HistoryTest()
        self.assertEqual(
            ({}, "Created settings. Settings: 5."), mix.construct_changes("Created settings.", "Settings: 5.", {})
        )

        self.assertEqual(
            ({"test_field": "pesa"}, 'Created settings. Settings: 5. Test Field set to "pesa"'),
            mix.construct_changes("Created settings.", "Settings: 5.", {"test_field": "pesa"}),
        )

        mix.id = 5
        mix.snapshot(previous=mix)

        self.assertEqual(({}, "Settings: 5."), mix.construct_changes("Created settings.", "Settings: 5.", {}))
        self.assertEqual(
            ({"test_field": "pesa"}, 'Settings: 5. Test Field set to "pesa"'),
            mix.construct_changes("Created settings.", "Settings: 5.", {"test_field": "pesa"}),
        )
        self.assertEqual(({}, "Settings: 5."), mix.construct_changes("Created settings.", "Settings: 5.", {}))
