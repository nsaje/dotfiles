import csv
import io
import json

from django.http.request import HttpRequest
from django.test import Client
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from mock import patch

from dash import constants
from dash import models
from utils import s3helpers
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.models import User


class PublisherTargetingViewTest(TestCase):
    fixtures = ["test_publishers.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

    def get_payload(self, **kwargs):
        payload = {"entries": [{"publisher": "cnn.com"}], "status": constants.PublisherTargetingStatus.BLACKLISTED}
        payload.update(kwargs)
        return payload

    def assertEntriesInserted(self, publisher_group, entry_dicts=None):
        entry_dicts = entry_dicts or [
            {"publisher": "cnn.com", "placement": None, "source": None, "include_subdomains": False}
        ]
        self.assertEqual(publisher_group.entries.count(), len(entry_dicts))
        entries = publisher_group.entries.all().values("publisher", "placement", "source", "include_subdomains")
        self.assertCountEqual(entry_dicts, entries)

    def test_post_not_allowed(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        payload = self.get_payload(ad_group=ad_group.id)

        response = self.client.post(reverse("publisher_targeting"), data=payload)
        self.assertEqual(response.status_code, 404)

    def test_post_ad_group(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        test_helper.add_permissions(self.user, ["can_modify_publisher_blacklist_status"])
        payload = self.get_payload(ad_group=ad_group.id)

        response = self.client.post(
            reverse("publisher_targeting"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEntriesInserted(ad_group.default_blacklist)

    def test_post_campaign_not_allowed(self):
        campaign = models.Campaign.objects.get(pk=1)
        test_helper.add_permissions(self.user, ["can_modify_publisher_blacklist_status"])
        payload = self.get_payload(campaign=campaign.id)

        response = self.client.post(
            reverse("publisher_targeting"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)

    def test_post_campaign(self):
        campaign = models.Campaign.objects.get(pk=1)
        test_helper.add_permissions(
            self.user,
            ["can_modify_publisher_blacklist_status", "can_access_campaign_account_publisher_blacklist_status"],
        )
        payload = self.get_payload(campaign=campaign.id)

        response = self.client.post(
            reverse("publisher_targeting"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        campaign.refresh_from_db()
        self.assertEntriesInserted(campaign.default_blacklist)

    def test_post_account_not_allowed(self):
        account = models.Account.objects.get(pk=1)
        test_helper.add_permissions(self.user, ["can_modify_publisher_blacklist_status"])
        payload = self.get_payload(account=account.id)

        response = self.client.post(
            reverse("publisher_targeting"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)

    def test_post_account(self):
        account = models.Account.objects.get(pk=1)
        test_helper.add_permissions(
            self.user,
            ["can_modify_publisher_blacklist_status", "can_access_campaign_account_publisher_blacklist_status"],
        )
        payload = self.get_payload(account=account.id)

        response = self.client.post(
            reverse("publisher_targeting"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        account.refresh_from_db()
        self.assertEntriesInserted(account.default_blacklist)

    def test_post_global_not_allowed(self):
        test_helper.add_permissions(self.user, ["can_modify_publisher_blacklist_status"])
        payload = self.get_payload()

        response = self.client.post(
            reverse("publisher_targeting"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)

    def test_post_global(self):
        global_group = models.PublisherGroup(name="imglobal")
        request = HttpRequest()
        request.user = self.user
        global_group.save(request)

        test_helper.add_permissions(
            self.user, ["can_modify_publisher_blacklist_status", "can_access_global_publisher_blacklist_status"]
        )
        payload = self.get_payload()

        with override_settings(GLOBAL_BLACKLIST_ID=global_group.id):
            response = self.client.post(
                reverse("publisher_targeting"), data=json.dumps(payload), content_type="application/json"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEntriesInserted(global_group)

    def test_post_placement_ad_group(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        test_helper.add_permissions(self.user, ["can_modify_publisher_blacklist_status", "can_use_placement_targeting"])
        payload = self.get_payload(ad_group=ad_group.id, entries=[{"publisher": "cnn.com", "placement": "widget1"}])

        response = self.client.post(
            reverse("publisher_targeting"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEntriesInserted(
            ad_group.default_blacklist,
            entry_dicts=[{"publisher": "cnn.com", "placement": "widget1", "source": None, "include_subdomains": False}],
        )

    def test_post_placement_ad_group_no_permission(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        test_helper.add_permissions(self.user, ["can_modify_publisher_blacklist_status"])
        payload = self.get_payload(ad_group=ad_group.id, entries=[{"publisher": "cnn.com", "placement": "widget1"}])

        response = self.client.post(
            reverse("publisher_targeting"), data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["data"]["errors"], {"entries": ["Invalid field: placement"]})


class PublisherGroupsViewTest(TestCase):

    fixtures = ["test_publishers.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

    def test_get_not_allowed(self):
        response = self.client.get(reverse("publisher_groups"), {"account_id": 1})
        self.assertEqual(response.status_code, 404)

    def test_get_with_account(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        account = models.Account.objects.get(pk=1)

        response = self.client.get(reverse("publisher_groups"), {"account_id": account.id})

        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        for pg in content["data"]["publisher_groups"]:
            # check user has permission for all the publisher groups returned
            self.assertEqual(models.PublisherGroup.objects.filter(pk=pg["id"]).filter_by_account(account).count(), 1)

    def test_get_with_agency(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        agency = magic_mixer.blend(models.Agency, users=[self.user])
        publisher_group = magic_mixer.blend(models.PublisherGroup, name="test publisher group", agency=agency)

        response = self.client.get(reverse("publisher_groups"), {"agency_id": agency.id})

        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(content["data"]["publisher_groups"]), 1)
        self.assertEqual(content["data"]["publisher_groups"][0]["id"], publisher_group.id)

        for pg in content["data"]["publisher_groups"]:
            # check user has permission for all the publisher groups returned
            self.assertEqual(models.PublisherGroup.objects.filter(pk=pg["id"]).filter_by_agency(agency).count(), 1)

    def test_get_without_agency_and_account(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        agency = magic_mixer.blend(models.Agency, users=[self.user])

        magic_mixer.blend(models.PublisherGroup, name="test publisher group", agency=agency)

        response = self.client.get(reverse("publisher_groups"))
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content["data"]["error_code"], "ValidationError")

    def test_get_not_implicit(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        account = models.Account.objects.get(pk=1)

        response = self.client.get(reverse("publisher_groups"), {"account_id": account.id, "not_implicit": True})

        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)

        for pg in content["data"]["publisher_groups"]:
            # check user has permission for all the publisher groups returned
            pgs = models.PublisherGroup.objects.filter(pk=pg["id"]).filter_by_account(account)
            self.assertEqual(pgs.count(), 1)
            self.assertFalse(pgs.first().implicit)


class PublisherGroupsUploadTest(TestCase):

    fixtures = ["test_publishers.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=2)
        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

    def test_get_not_allowed(self):
        response = self.client.get(reverse("publisher_groups_upload", kwargs={"csv_key": "asd"}), {"account_id": 1})
        self.assertEqual(response.status_code, 404)

    def test_post_not_allowed(self):
        response = self.client.post(reverse("publisher_groups_upload"), {"account_id": 1})
        self.assertEqual(response.status_code, 404)

    @patch.object(s3helpers.S3Helper, "get")
    def test_get(self, mock_s3):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])

        response = self.client.get(reverse("publisher_groups_upload", kwargs={"csv_key": "asd"}), {"account_id": 1})

        self.assertEqual(response.status_code, 200)
        mock_s3.assert_called_with("publisher_group_errors/account_1/asd.csv")

    def test_post_update(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        account = models.Account.objects.get(pk=1)
        data = {"id": 1, "name": "qweasd", "include_subdomains": True, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 200)
        publisher_group = models.PublisherGroup.objects.get(pk=1)
        self.assertEqual(publisher_group.name, "qweasd")
        for entry in publisher_group.entries.all():
            self.assertEqual(entry.include_subdomains, True)

    def test_post_update_apply_include_subdomains(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        account = models.Account.objects.get(pk=1)
        data = {"id": 1, "name": "qweasd", "include_subdomains": False, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 200)
        publisher_group = models.PublisherGroup.objects.get(pk=1)
        self.assertEqual(publisher_group.name, "qweasd")
        for entry in publisher_group.entries.all():
            self.assertEqual(entry.include_subdomains, False)

    @staticmethod
    def _create_file_content(rows):
        csv_file = io.StringIO()
        field_names = rows[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)
        csv_file.flush()
        csv_file.seek(0)
        return csv_file.read()

    def test_post_create_publisher_source(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        account = models.Account.objects.get(pk=1)
        rows = [{"Publisher": "asd", "Source": ""}, {"Publisher": "qwe", "Source": "adsnative"}]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)

        self.assertEqual(response["data"]["name"], "qweasd")

        publisher_group = models.PublisherGroup.objects.get(pk=response["data"]["id"])
        self.assertEqual(publisher_group.name, "qweasd")
        for i, entry in enumerate(publisher_group.entries.all()):
            self.assertEqual(entry.publisher, rows[i]["Publisher"])
            self.assertEqual(entry.source.bidder_slug if entry.source else None, rows[i]["Source"] or None)
            self.assertEqual(entry.include_subdomains, True)

    def test_post_create_publisher(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        account = models.Account.objects.get(pk=1)
        rows = [{"Publisher": "asd"}, {"Publisher": "qwe"}]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)

        self.assertEqual(response["data"]["name"], "qweasd")

        publisher_group = models.PublisherGroup.objects.get(pk=response["data"]["id"])
        self.assertEqual(publisher_group.name, "qweasd")
        for i, entry in enumerate(publisher_group.entries.all()):
            self.assertEqual(entry.publisher, rows[i]["Publisher"])
            self.assertIsNone(entry.source)
            self.assertEqual(entry.include_subdomains, True)

    def test_post_create_publisher_source_placement_no_permission(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        account = models.Account.objects.get(pk=1)
        rows = [
            {"Publisher": "asd", "Placement": "widget1", "Source": ""},
            {"Publisher": "qwe", "Placement": "widget2", "Source": "adsnative"},
        ]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertEqual(response.json()["data"]["errors"]["entries"], ['Column "Placement" is not supported'])

    def test_post_create_publisher_source_placement(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups", "can_use_placement_targeting"])
        account = models.Account.objects.get(pk=1)
        rows = [
            {"Publisher": "asd", "Placement": "widget1", "Source": ""},
            {"Publisher": "qwe", "Placement": "widget2", "Source": "adsnative"},
        ]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)

        self.assertEqual(response["data"]["name"], "qweasd")

        publisher_group = models.PublisherGroup.objects.get(pk=response["data"]["id"])
        self.assertEqual(publisher_group.name, "qweasd")
        for i, entry in enumerate(publisher_group.entries.all()):
            self.assertEqual(entry.publisher, rows[i]["Publisher"])
            self.assertEqual(entry.placement, rows[i]["Placement"])
            self.assertEqual(entry.source.bidder_slug if entry.source else None, rows[i]["Source"] or None)
            self.assertEqual(entry.include_subdomains, True)

    def test_post_create_publisher_placement_no_permission(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        account = models.Account.objects.get(pk=1)
        rows = [{"Publisher": "asd", "Placement": "widget1"}, {"Publisher": "qwe", "Placement": "widget2"}]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertEqual(response.json()["data"]["errors"]["entries"], ['Column "Placement" is not supported'])

    def test_post_create_publisher_placement(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups", "can_use_placement_targeting"])
        account = models.Account.objects.get(pk=1)
        rows = [{"Publisher": "asd", "Placement": "widget1"}, {"Publisher": "qwe", "Placement": "widget2"}]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)

        self.assertEqual(response["data"]["name"], "qweasd")

        publisher_group = models.PublisherGroup.objects.get(pk=response["data"]["id"])
        self.assertEqual(publisher_group.name, "qweasd")
        for i, entry in enumerate(publisher_group.entries.all()):
            self.assertEqual(entry.publisher, rows[i]["Publisher"])
            self.assertEqual(entry.placement, rows[i]["Placement"])
            self.assertIsNone(entry.source)
            self.assertEqual(entry.include_subdomains, True)

    def test_post_create_unknown_columns(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups", "can_use_placement_targeting"])
        account = models.Account.objects.get(pk=1)
        rows = [{"Publisher": "asd", "Unknown": "foo"}, {"Publisher": "qwe", "Unknown": "bar"}]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertEqual(response.json()["data"]["errors"]["entries"], ['Column "Unknown" is not supported'])

    def test_post_create_publisher_mixed_entries(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups", "can_use_placement_targeting"])
        account = models.Account.objects.get(pk=1)
        rows = [
            {"Publisher": "qwe", "Placement": "", "Source": ""},
            {"Publisher": "qwe", "Placement": "", "Source": "adsnative"},
            {"Publisher": "qwe", "Placement": "widget1", "Source": "adsnative"},
            {"Publisher": "qwe", "Placement": "widget1", "Source": ""},
        ]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)

        self.assertEqual(response["data"]["name"], "qweasd")

        publisher_group = models.PublisherGroup.objects.get(pk=response["data"]["id"])
        self.assertEqual(publisher_group.name, "qweasd")
        for i, entry in enumerate(publisher_group.entries.all()):
            self.assertEqual(entry.publisher, rows[i]["Publisher"] or None)
            self.assertEqual(entry.placement, rows[i]["Placement"] or None)
            self.assertEqual(entry.source.bidder_slug if entry.source else None, rows[i]["Source"] or None)
            self.assertEqual(entry.include_subdomains, True)

    def test_post_create_publisher_optional_in_column_names(self):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups", "can_use_placement_targeting"])
        account = models.Account.objects.get(pk=1)
        rows = [
            {"Publisher": "qwe", "Placement (optional)": "", "Source (optional)": ""},
            {"Publisher": "qwe", "Placement (optional)": "", "Source (optional)": "adsnative"},
            {"Publisher": "qwe", "Placement (optional)": "widget1", "Source (optional)": "adsnative"},
            {"Publisher": "qwe", "Placement (optional)": "widget1", "Source (optional)": ""},
        ]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)

        self.assertEqual(response["data"]["name"], "qweasd")

        publisher_group = models.PublisherGroup.objects.get(pk=response["data"]["id"])
        self.assertEqual(publisher_group.name, "qweasd")
        for i, entry in enumerate(publisher_group.entries.all()):
            self.assertEqual(entry.publisher, rows[i]["Publisher"] or None)
            self.assertEqual(entry.placement, rows[i]["Placement (optional)"] or None)
            self.assertEqual(entry.source.bidder_slug if entry.source else None, rows[i]["Source (optional)"] or None)
            self.assertEqual(entry.include_subdomains, True)

    @patch.object(s3helpers.S3Helper, "put")
    def test_post_create_publisher_mixed_entries_errors(self, mock_s3):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups", "can_use_placement_targeting"])
        account = models.Account.objects.get(pk=1)
        rows = [
            {"Publisher": "", "Placement": "", "Source": ""},
            {"Publisher": "qwe", "Placement": "", "Source": "asw"},
            {"Publisher": "qwe", "Placement": "widget1", "Source": "asw"},
            {"Publisher": "qwe", "Placement": "widget1", "Source": ""},
            {"Publisher": "", "Placement": "widget1", "Source": ""},
            {"Publisher": "", "Placement": "widget1", "Source": "asw"},
            {"Publisher": "", "Placement": "", "Source": "asw"},
            {"Publisher": "qwe", "Placement": "Not reported", "Source": ""},
        ]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 400)
        self.assertTrue(mock_s3.called)
        error_file_contents = mock_s3.call_args_list[0][0][1]

        rows = [row for row in csv.DictReader(io.StringIO(error_file_contents))]

        self.assertEqual(
            rows,
            [
                {"Publisher": "qwe", "Placement": "", "Source": "asw", "Error": "Unknown source"},
                {"Publisher": "qwe", "Placement": "widget1", "Source": "asw", "Error": "Unknown source"},
                {"Publisher": "qwe", "Placement": "widget1", "Source": "", "Error": ""},
                {"Publisher": "", "Placement": "widget1", "Source": "", "Error": "Publisher is required"},
                {
                    "Publisher": "",
                    "Placement": "widget1",
                    "Source": "asw",
                    "Error": "Publisher is required; Unknown source",
                },
                {"Publisher": "", "Placement": "", "Source": "asw", "Error": "Publisher is required; Unknown source"},
                {
                    "Publisher": "qwe",
                    "Placement": "Not reported",
                    "Source": "",
                    "Error": 'Invalid placement: "Not reported"',
                },
            ],
        )

    @patch.object(s3helpers.S3Helper, "put")
    def test_post_create_publisher_mixed_entries_errors_no_permission(self, mock_s3):
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        account = models.Account.objects.get(pk=1)
        rows = [
            {"Publisher": "", "Source": ""},
            {"Publisher": "qwe", "Source": "asw"},
            {"Publisher": "qwe", "Source": ""},
            {"Publisher": "", "Source": "asw"},
        ]

        mock_file = test_helper.mock_file("asd.csv", self._create_file_content(rows))
        data = {"name": "qweasd", "include_subdomains": True, "entries": mock_file, "account_id": account.id}

        response = self.client.post(reverse("publisher_groups_upload"), data=data)

        self.assertEqual(response.status_code, 400)
        self.assertTrue(mock_s3.called)
        error_file_contents = mock_s3.call_args_list[0][0][1]

        rows = [row for row in csv.DictReader(io.StringIO(error_file_contents))]

        self.assertEqual(
            rows,
            [
                {"Publisher": "qwe", "Source": "asw", "Error": "Unknown source"},
                {"Publisher": "qwe", "Source": "", "Error": ""},
                {"Publisher": "", "Source": "asw", "Error": "Publisher is required; Unknown source"},
            ],
        )


class PublisherGroupsDownloadTest(TestCase):
    def setUp(self):
        self.user = self.user = magic_mixer.blend(User, password="md5$4kOz9CyKkLMC$007d0be660d98888686dcf3c3688262c")
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

        self.agency = magic_mixer.blend(models.Agency)
        self.agency.users.add(self.user)
        self.account = magic_mixer.blend(models.Account, agency=self.agency)
        self.account.users.add(self.user)
        self.source = magic_mixer.blend(models.Source, bidder_slug="somesource")
        self.publisher_group = magic_mixer.blend(models.PublisherGroup, account=self.account)
        self.publisher_group_entries = [
            magic_mixer.blend(
                models.PublisherGroupEntry, publisher_group=self.publisher_group, publisher="example.com"
            ),
            magic_mixer.blend(
                models.PublisherGroupEntry,
                publisher_group=self.publisher_group,
                publisher="example.com",
                source=self.source,
            ),
            magic_mixer.blend(
                models.PublisherGroupEntry,
                publisher_group=self.publisher_group,
                publisher="example.com",
                source=self.source,
                placement="someplacement",
            ),
            magic_mixer.blend(
                models.PublisherGroupEntry,
                publisher_group=self.publisher_group,
                publisher="example.com",
                placement="someplacement",
            ),
        ]

    def test_get_without_placement_permission(self):
        models.PublisherGroupEntry.objects.filter(publisher_group=self.publisher_group).exclude(placement=None).delete()
        response = self.client.get(
            reverse("download_publisher_groups", kwargs={"publisher_group_id": self.publisher_group.id}),
            data={"account_id": self.account.id},
        )

        self.assertEqual(response.status_code, 200)
        rows = [row for row in csv.DictReader(io.StringIO(response.content.decode()))]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (
                    ("Publisher", e.publisher if e.publisher is not None else ""),
                    ("Source", e.source.bidder_slug if e.source is not None else ""),
                )
                for e in self.publisher_group_entries
            },
        )

    def test_get_without_placement_permission_existing_placement_entry(self):
        response = self.client.get(
            reverse("download_publisher_groups", kwargs={"publisher_group_id": self.publisher_group.id}),
            data={"account_id": self.account.id},
        )

        self.assertEqual(response.status_code, 200)
        rows = [row for row in csv.DictReader(io.StringIO(response.content.decode()))]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (
                    ("Publisher", e.publisher if e.publisher is not None else ""),
                    ("Placement", e.placement if e.placement is not None else ""),
                    ("Source", e.source.bidder_slug if e.source is not None else ""),
                )
                for e in self.publisher_group_entries
            },
        )

    def test_get_with_placement_permission(self):
        test_helper.add_permissions(self.user, ["can_use_placement_targeting"])
        response = self.client.get(
            reverse("download_publisher_groups", kwargs={"publisher_group_id": self.publisher_group.id}),
            data={"account_id": self.account.id},
        )

        self.assertEqual(response.status_code, 200)
        rows = [row for row in csv.DictReader(io.StringIO(response.content.decode()))]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (
                    ("Publisher", e.publisher if e.publisher is not None else ""),
                    ("Placement", e.placement if e.placement is not None else ""),
                    ("Source", e.source.bidder_slug if e.source is not None else ""),
                )
                for e in self.publisher_group_entries
            },
        )


class PublisherGroupsExampleDownloadTest(TestCase):
    def setUp(self):
        self.user = self.user = magic_mixer.blend(User, password="md5$4kOz9CyKkLMC$007d0be660d98888686dcf3c3688262c")
        test_helper.add_permissions(self.user, ["can_edit_publisher_groups"])
        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

    def test_get_without_placement_permission(self):
        response = self.client.get(reverse("publisher_groups_example"))

        self.assertEqual(response.status_code, 200)
        rows = [row for row in csv.DictReader(io.StringIO(response.content.decode()))]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (("Publisher", "example.com"), ("Source (optional)", "")),
                (("Publisher", "some.example.com"), ("Source (optional)", "")),
            },
        )

    def test_get_with_placement_permission(self):
        test_helper.add_permissions(self.user, ["can_use_placement_targeting"])
        response = self.client.get(reverse("publisher_groups_example"))

        self.assertEqual(response.status_code, 200)
        rows = [row for row in csv.DictReader(io.StringIO(response.content.decode()))]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (("Publisher", "example.com"), ("Placement (optional)", ""), ("Source (optional)", "")),
                (("Publisher", "some.example.com"), ("Placement (optional)", ""), ("Source (optional)", "")),
            },
        )
