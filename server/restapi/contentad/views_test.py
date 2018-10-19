import mock
import json

from restapi.common.views_base_test import RESTAPITest
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from zemauth.models import User

import utils.test_helper
import dash.models
from dash.features import contentupload
from dash import constants
from . import views


class ContentAdsTest(RESTAPITest):
    @classmethod
    def contentad_repr(
        cls,
        id=1,
        ad_group_id=1,
        state=constants.ContentAdSourceState.ACTIVE,
        url="https://www.example.com",
        title="My title",
        image_url="https://www.example.com/img",
        display_url="https://www.example.com/landing",
        brand_name="My brand",
        description="My description",
        call_to_action="Read more...",
        label="My label",
        image_crop="center",
        tracker_urls=[],
    ):
        representation = {
            "id": str(id),
            "adGroupId": str(ad_group_id),
            "state": constants.ContentAdSourceState.get_name(state),
            "url": url,
            "title": title,
            "imageUrl": image_url,
            "displayUrl": display_url,
            "brandName": brand_name,
            "description": description,
            "callToAction": call_to_action,
            "label": label,
            "imageCrop": image_crop,
            "trackerUrls": tracker_urls,
        }
        return cls.normalize(representation)

    def validate_against_db(self, cad):
        cad_db = dash.models.ContentAd.objects.get(pk=cad["id"])
        expected = self.contentad_repr(
            id=cad_db.pk,
            ad_group_id=cad_db.ad_group_id,
            state=cad_db.state,
            url=cad_db.url,
            title=cad_db.title,
            image_url=cad_db.get_image_url(),
            display_url=cad_db.display_url,
            brand_name=cad_db.brand_name,
            description=cad_db.description,
            call_to_action=cad_db.call_to_action,
            label=cad_db.label,
            image_crop=cad_db.image_crop,
            tracker_urls=cad_db.tracker_urls,
        )
        self.assertEqual(expected, cad)

    def test_contentads_list(self):
        r = self.client.get(reverse("contentads_list") + "?adGroupId=2040")
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_contentads_get(self):
        r = self.client.get(reverse("contentads_details", kwargs={"content_ad_id": 16805}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_contentads_get_permissioned(self):
        utils.test_helper.add_permissions(self.user, ["can_use_ad_additional_data"])
        r = self.client.get(reverse("contentads_details", kwargs={"content_ad_id": 16805}))
        resp_json = self.assertResponseValid(r)
        self.assertIn("additionalData", resp_json["data"])

    def test_contentads_put(self):
        r = self.client.put(
            reverse("contentads_details", kwargs={"content_ad_id": 16805}),
            data={"state": "INACTIVE", "label": "My new label"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["state"], "INACTIVE")
        self.assertEqual(resp_json["data"]["label"], "My new label")

    def test_contentads_put_permissioned(self):
        self.client.put(
            reverse("contentads_details", kwargs={"content_ad_id": 16805}),
            data={"additionalData": {"a": 1}},
            format="json",
        )
        cad = dash.models.ContentAd.objects.get(pk=16805)
        self.assertEqual(cad.additional_data, None)

    def test_contentads_put_url(self):
        content_ad = dash.models.ContentAd.objects.get(pk=16805)
        views.ACCOUNTS_CAN_EDIT_URL.append(content_ad.ad_group.campaign.account_id)
        r = self.client.put(
            reverse("contentads_details", kwargs={"content_ad_id": content_ad.pk}),
            data={"state": "INACTIVE", "url": "https://example.com"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["state"], "INACTIVE")
        self.assertEqual(resp_json["data"]["url"], "https://example.com")

    def test_contentads_put_updates(self):
        content_ad = dash.models.ContentAd.objects.get(pk=16805)
        r = self.client.put(
            reverse("contentads_details", kwargs={"content_ad_id": content_ad.pk}),
            data={"trackerUrls": ["test1", "test2"], "title": "newtitle"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["trackerUrls"], ["test1", "test2"])
        self.assertNotEqual(resp_json["data"]["title"], "newtitle")  # readonly


@override_settings(R1_DEMO_MODE=True)
class TestBatchUpload(TestCase):
    fixtures = ["test_views.yaml"]

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.get(pk=1))

    @staticmethod
    def _mock_content_ad(title):
        return {
            "state": "ACTIVE",
            "url": "https://www.example.com/p/83895c0e-3bbe-4ad7-a0f6-c1917788ceb9",
            "title": title,
            "imageUrl": "http://example.com/p/srv/9018/e5d6adb68f1d404f82541e335c50bbd3.jpg?w=1024&h=768&fit=crop&crop=center&fm=jpg",
            "displayUrl": "kuhic.com",
            "brandName": "Kassulke-Hartmann",
            "description": "People really should avert their gaze from the modern survival thinking for just a bit and also look at how folks 150 years ago did it.",
            "callToAction": "Watch More",
            "label": "",
            "imageCrop": "center",
            "trackerUrls": ["https://www.example.com/a", "https://www.example.com/b"],
        }

    @mock.patch("dash.features.contentupload.upload._invoke_external_validation", mock.Mock())
    def test_batch_upload_success(self):
        to_upload = [self._mock_content_ad("test1"), self._mock_content_ad("test2")]
        r = self.client.post(reverse("contentads_batch_list") + "?adGroupId=987", to_upload, format="json")
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertIn("id", resp_json["data"])

        batch_id = int(resp_json["data"]["id"])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse("contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        self._approve_candidates(batch)

        r = self.client.get(reverse("contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "DONE")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        saved_content_ads = batch.contentad_set.all().order_by("pk")
        self.assertEqual(len(to_upload), len(resp_json["data"]["approvedContentAds"]))
        self.assertEqual(len(to_upload), len(saved_content_ads))
        for i in range(len(to_upload)):
            for field in (
                "state",
                "title",
                "displayUrl",
                "brandName",
                "description",
                "callToAction",
                "label",
                "trackerUrls",
            ):
                self.assertEqual(to_upload[i][field], resp_json["data"]["approvedContentAds"][i][field])
            self.assertEqual(saved_content_ads[i].id, int(resp_json["data"]["approvedContentAds"][i]["id"]))

    @staticmethod
    def _approve_candidates(batch):
        for candidate in batch.contentadcandidate_set.all():
            candidate.image_id = "p/srv/8678/13f72b5e37a64860a73ac95ff51b2a3e"
            candidate.image_hash = "1234"
            candidate.image_height = 500
            candidate.image_width = 500
            candidate.image_status = constants.AsyncUploadJobStatus.OK
            candidate.url_status = constants.AsyncUploadJobStatus.OK
            candidate.save()
        contentupload.upload._handle_auto_save(batch)

    @mock.patch("dash.features.contentupload.upload._invoke_external_validation", mock.Mock())
    def test_batch_upload_failure(self):
        to_upload = [self._mock_content_ad("test1"), self._mock_content_ad("test2")]
        r = self.client.post(reverse("contentads_batch_list") + "?adGroupId=987", to_upload, format="json")
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertIn("id", resp_json["data"])

        batch_id = int(resp_json["data"]["id"])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse("contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        self._reject_candidates(batch)

        r = self.client.get(reverse("contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "FAILED")
        self.assertEqual(resp_json["data"]["approvedContentAds"], [])
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

    @staticmethod
    def _reject_candidates(batch):
        for candidate in batch.contentadcandidate_set.all():
            candidate.image_status = constants.AsyncUploadJobStatus.FAILED
            candidate.url_status = constants.AsyncUploadJobStatus.FAILED
            candidate.save()
        contentupload.upload._handle_auto_save(batch)
