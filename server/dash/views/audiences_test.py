# -*- coding: utf-8 -*-
import json

import mock
from django.conf import settings
from django.urls import reverse

from dash import constants
from dash import models
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth import models as zmodels


class AudiencesTestCase(BaseTestCase):
    fixtures = ["test_audiences.yaml"]

    def setUp(self):
        self.original_k1_demo_mode = settings.K1_DEMO_MODE
        settings.K1_DEMO_MODE = True

        self.user = zmodels.User.objects.get(pk=3)
        self.assertFalse(self.user.is_superuser)
        self.client.login(username=self.user.email, password="secret")

    def tearDown(self):
        settings.K1_DEMO_MODE = self.original_k1_demo_mode

    def _get_valid_post_data(self):
        return {
            "name": "Test Audience",
            "pixel_id": 1,
            "ttl": 90,
            "prefill_days": 90,
            "rules": [{"type": constants.AudienceRuleType.CONTAINS, "value": "test"}],
        }

    def test_account_permissions(self):
        self.user = zmodels.User.objects.get(pk=2)
        self.assertFalse(self.user.is_superuser)
        self.client.login(username=self.user.email, password="secret")

        url = reverse("accounts_audience", kwargs={"account_id": 2, "audience_id": 5})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 404)

        url = reverse("accounts_audiences", kwargs={"account_id": 2})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_no_account(self):
        url = reverse("accounts_audience", kwargs={"account_id": 5, "audience_id": 5})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response_dict = {
            "success": False,
            "data": {"message": "Account does not exist", "error_code": "MissingDataError"},
        }
        self.assertEqual(json.loads(response.content), response_dict)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), response_dict)

        url = reverse("accounts_audiences", kwargs={"account_id": 5})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), response_dict)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), response_dict)

    def test_get_audience_wrong_account(self):
        url = reverse("accounts_audience", kwargs={"account_id": 1, "audience_id": 5})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response_dict = {
            "success": False,
            "data": {"message": "Audience does not exist", "error_code": "MissingDataError"},
        }
        self.assertEqual(json.loads(response.content), response_dict)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), response_dict)

    def test_get_audience(self):
        url = reverse("accounts_audience", kwargs={"account_id": 1, "audience_id": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_dict = {
            "success": True,
            "data": {
                "pixel_id": "1",
                "rules": [{"type": 1, "id": "1", "value": "test"}],
                "ttl": 90,
                "prefill_days": 180,
                "id": "1",
                "name": "test audience 1",
            },
        }
        self.assertEqual(json.loads(response.content), response_dict)

    @mock.patch("redshiftapi.api_audiences.get_audience_sample_size")
    def test_get_audiences(self, redshift_mock):
        def side_effect(*args):
            return 10 if args[2] != 1 else 1

        redshift_mock.side_effect = side_effect

        url = reverse("accounts_audiences", kwargs={"account_id": 1}) + "?include_size=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_dict = {
            "success": True,
            "data": [
                {
                    "count": 1000,
                    "count_yesterday": 100,
                    "id": "1",
                    "name": "test audience 1",
                    "archived": False,
                    "created_dt": "2015-08-25T05:58:21",
                },
                {
                    "count": 1000,
                    "count_yesterday": 100,
                    "id": "2",
                    "name": "test audience 2",
                    "archived": False,
                    "created_dt": "2015-08-25T05:58:21",
                },
                {
                    "count": 1000,
                    "count_yesterday": 100,
                    "id": "4",
                    "name": "test audience 4",
                    "archived": False,
                    "created_dt": "2015-08-25T05:58:21",
                },
            ],
        }
        self.assertEqual(json.loads(response.content), response_dict)

        redshift_mock.assert_has_calls(
            [
                mock.call(1, "1", 90, mock.ANY),
                mock.call(1, "1", 1, mock.ANY),
                mock.call(1, "1", 90, mock.ANY),
                mock.call(1, "1", 1, mock.ANY),
                mock.call(1, "2", 90, mock.ANY),
                mock.call(1, "2", 1, mock.ANY),
            ]
        )

    def test_get_audiences_include_archived(self):
        url = reverse("accounts_audiences", kwargs={"account_id": 1})
        response = self.client.get(url + "?include_archived=1")
        self.assertEqual(response.status_code, 200)
        response_dict = {
            "success": True,
            "data": [
                {
                    "count": None,
                    "count_yesterday": None,
                    "id": "1",
                    "name": "test audience 1",
                    "archived": False,
                    "created_dt": "2015-08-25T05:58:21",
                },
                {
                    "count": None,
                    "count_yesterday": None,
                    "id": "2",
                    "name": "test audience 2",
                    "archived": False,
                    "created_dt": "2015-08-25T05:58:21",
                },
                {
                    "count": None,
                    "count_yesterday": None,
                    "id": "3",
                    "name": "test audience 3",
                    "archived": True,
                    "created_dt": "2015-08-25T05:58:21",
                },
                {
                    "count": None,
                    "count_yesterday": None,
                    "id": "4",
                    "name": "test audience 4",
                    "archived": False,
                    "created_dt": "2015-08-25T05:58:21",
                },
            ],
        }
        self.assertEqual(json.loads(response.content), response_dict)

    @mock.patch("utils.k1_helper.update_account")
    def test_post(self, k1_update_account_mock):
        data = self._get_valid_post_data()
        del (data["prefill_days"])
        url = reverse("accounts_audiences", kwargs={"account_id": 1})

        audiences = models.Audience.objects.filter(pk=6)
        self.assertEqual(len(audiences), 0)

        rules = models.AudienceRule.objects.filter(pk=6)
        self.assertEqual(len(rules), 0)

        history = models.History.objects.all()
        self.assertEqual(len(history), 0)

        response = self.client.post(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_dict = {
            "success": True,
            "data": {
                "pixel_id": "1",
                "rules": [{"id": "6", "type": 2, "value": "test"}],
                "ttl": 90,
                "prefill_days": 90,
                "id": "6",
                "name": "Test Audience",
            },
        }
        self.assertEqual(json.loads(response.content), response_dict)

        audiences = models.Audience.objects.filter(pk=6)
        self.assertEqual(len(audiences), 1)
        self.assertEqual(audiences[0].name, "Test Audience")
        self.assertEqual(audiences[0].pixel_id, 1)
        self.assertEqual(audiences[0].archived, False)
        self.assertEqual(audiences[0].ttl, 90)
        self.assertEqual(audiences[0].prefill_days, 90)
        self.assertEqual(audiences[0].created_by_id, 3)

        rules = models.AudienceRule.objects.filter(pk=6)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].audience_id, 6)
        self.assertEqual(rules[0].type, constants.AudienceRuleType.CONTAINS)
        self.assertEqual(rules[0].value, "test")

        history = models.History.objects.all()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].agency, None)
        self.assertEqual(history[0].account_id, 1)
        self.assertEqual(history[0].campaign, None)
        self.assertEqual(history[0].ad_group, None)
        self.assertEqual(history[0].level, constants.HistoryLevel.ACCOUNT)
        self.assertEqual(history[0].action_type, constants.HistoryActionType.AUDIENCE_CREATE)
        self.assertEqual(history[0].changes_text, 'Created audience "Test Audience".')
        self.assertEqual(history[0].changes, None)
        self.assertEqual(history[0].created_by_id, 3)

        k1_update_account_mock.assert_called_with(audiences[0].pixel.account, msg="audience.create")

    @mock.patch("utils.k1_helper.update_account")
    def test_put(self, k1_update_account_mock):
        # ttl work, but not rules
        data = {"name": "New name", "rules": [{"id": "1", "type": 1, "value": "teeeeest"}]}
        url = reverse("accounts_audience", kwargs={"account_id": 1, "audience_id": 1})

        response = self.client.put(url, json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_dict = {
            "success": True,
            "data": {
                "pixel_id": "1",
                "rules": [{"id": "1", "type": 1, "value": "test"}],
                "ttl": 90,
                "prefill_days": 180,
                "id": "1",
                "name": "New name",
            },
        }
        self.assertEqual(json.loads(response.content), response_dict)

        audiences = models.Audience.objects.filter(pk=1)
        self.assertEqual(audiences[0].name, "New name")
        self.assertEqual(audiences[0].pixel_id, 1)
        self.assertEqual(audiences[0].archived, False)
        self.assertEqual(audiences[0].ttl, 90)
        self.assertEqual(audiences[0].prefill_days, 180)
        self.assertEqual(audiences[0].created_by_id, 1)

        rules = audiences[0].audiencerule_set.all()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].audience_id, 1)
        self.assertEqual(rules[0].type, constants.AudienceRuleType.STARTS_WITH)
        self.assertEqual(rules[0].value, "test")

        history = models.History.objects.all()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].agency, None)
        self.assertEqual(history[0].account_id, 1)
        self.assertEqual(history[0].campaign, None)
        self.assertEqual(history[0].ad_group, None)
        self.assertEqual(history[0].level, constants.HistoryLevel.ACCOUNT)
        self.assertEqual(history[0].action_type, constants.HistoryActionType.AUDIENCE_UPDATE)
        self.assertEqual(history[0].changes_text, "Changed name of audience with ID 1 to 'New name'.")
        self.assertEqual(history[0].changes, None)
        self.assertEqual(history[0].created_by_id, 3)

        k1_update_account_mock.assert_called_with(audiences[0].pixel.account, msg="audience.update")


class AudienceArchiveTestCase(BaseTestCase):
    fixtures = ["test_audiences.yaml"]

    def setUp(self):
        self.user = zmodels.User.objects.get(pk=3)
        self.assertFalse(self.user.is_superuser)
        self.client.login(username=self.user.email, password="secret")
        magic_mixer.blend(models.Campaign, account_id=1, id=124, name="Campaign 0").save(None)
        magic_mixer.blend(models.AdGroup, campaign_id=124, id=125, name="Adgroup 0 ").save(None)

    def test_account_permissions(self):
        self.user = zmodels.User.objects.get(pk=2)
        self.assertFalse(self.user.is_superuser)
        self.client.login(username=self.user.email, password="secret")

        url = reverse("accounts_audience_archive", kwargs={"account_id": 2, "audience_id": 5})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

        url = reverse("accounts_audience_archive", kwargs={"account_id": 1, "audience_id": 5})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_archive(self):
        url = reverse("accounts_audience_archive", kwargs={"account_id": 1, "audience_id": 1})

        audiences = models.Audience.objects.filter(pk=1)
        self.assertEqual(audiences[0].archived, False)

        response = self.client.post(url, None, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_dict = {"success": True}
        self.assertEqual(json.loads(response.content), response_dict)

        audiences = models.Audience.objects.filter(pk=1)
        self.assertEqual(len(audiences), 1)
        self.assertEqual(audiences[0].archived, True)

        history = models.History.objects.last()
        self.assertTrue(history)
        self.assertEqual(history.agency, None)
        self.assertEqual(history.account_id, 1)
        self.assertEqual(history.campaign, None)
        self.assertEqual(history.ad_group, None)
        self.assertEqual(history.level, constants.HistoryLevel.ACCOUNT)
        self.assertEqual(history.action_type, constants.HistoryActionType.AUDIENCE_ARCHIVE)
        self.assertEqual(history.changes_text, "Archived audience 'test audience 1'.")
        self.assertEqual(history.changes, None)
        self.assertEqual(history.created_by_id, 3)

    def test_archive_while_audience_used_on_adgroup(self):
        audience = models.Audience.objects.get(id=1)
        adgroup = models.AdGroup.objects.get(id=125)

        #  Set the audience as audience targeting on the adgroup
        adgroup.settings.update(None, audience_targeting=[audience.id])
        self.assertFalse(audience.archived)
        self.assertTrue(adgroup.settings.audience_targeting)

        adgroups_used_on_audiences = audience.get_ad_groups_using_audience()
        self.assertIn(adgroup.id, [audi.id for audi in adgroups_used_on_audiences])
        self.assertFalse(audience.can_archive())

        response = self.client.post(
            reverse("accounts_audience_archive", kwargs={"account_id": 1, "audience_id": 1}),
            None,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.content)["data"],
            {
                "error_code": "ValidationError",
                "message": None,
                "errors": "Audience 'test audience 1' is currently targeted on ad groups Adgroup 0 .",
                "data": None,
            },
        )

        history_text = models.History.objects.all().first().changes_text
        self.assertNotEqual("Archived audience 'test audience 1'.", history_text)


class AudienceRestoreTestCase(BaseTestCase):
    fixtures = ["test_audiences.yaml"]

    def setUp(self):
        self.user = zmodels.User.objects.get(pk=3)
        self.assertFalse(self.user.is_superuser)
        self.client.login(username=self.user.email, password="secret")

    def test_account_permissions(self):
        self.user = zmodels.User.objects.get(pk=2)
        self.assertFalse(self.user.is_superuser)
        self.client.login(username=self.user.email, password="secret")

        url = reverse("accounts_audience_archive", kwargs={"account_id": 2, "audience_id": 5})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_restore(self):
        url = reverse("accounts_audience_restore", kwargs={"account_id": 1, "audience_id": 3})

        audiences = models.Audience.objects.filter(pk=3)
        self.assertEqual(audiences[0].archived, True)

        history = models.History.objects.all()
        self.assertEqual(len(history), 0)

        response = self.client.post(url, None, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_dict = {"success": True}
        self.assertEqual(json.loads(response.content), response_dict)

        audiences = models.Audience.objects.filter(pk=3)
        self.assertEqual(len(audiences), 1)
        self.assertEqual(audiences[0].archived, False)

        history = models.History.objects.all()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].agency, None)
        self.assertEqual(history[0].account_id, 1)
        self.assertEqual(history[0].campaign, None)
        self.assertEqual(history[0].ad_group, None)
        self.assertEqual(history[0].level, constants.HistoryLevel.ACCOUNT)
        self.assertEqual(history[0].action_type, constants.HistoryActionType.AUDIENCE_RESTORE)
        self.assertEqual(history[0].changes_text, "Restored audience 'test audience 3'.")
        self.assertEqual(history[0].changes, None)
        self.assertEqual(history[0].created_by_id, 3)
