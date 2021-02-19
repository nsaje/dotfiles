import json

import mock
from django.urls import reverse
from rest_framework.test import APIClient

import core.features.videoassets
import core.models
import dash.models
import utils.test_helper
from dash import constants
from dash.features import contentupload
from restapi.common.views_base_test_case import RESTAPITestCase
from restapi.contentad.v1 import views
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class ContentAdsTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        utils.test_helper.add_permissions(self.user, ["fea_can_change_campaign_type_to_display"])
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=self.account)

    @classmethod
    def contentad_repr(
        cls,
        id=None,
        ad_group_id=None,
        state=constants.ContentAdSourceState.ACTIVE,
        url="https://www.example.com",
        title="My title",
        image_url="https://www.example.com/img",
        icon_url="https://www.example.com/icon",
        display_url="https://www.example.com/landing",
        brand_name="My brand",
        description="My description",
        call_to_action="Read more...",
        label="My label",
        image_crop="center",
        tracker_urls=[],
        trackers=[],
    ):
        representation = {
            "id": str(id) if id is not None else None,
            "adGroupId": str(ad_group_id) if ad_group_id is not None else None,
            "state": constants.ContentAdSourceState.get_name(state),
            "url": url,
            "title": title,
            "imageUrl": image_url,
            "iconUrl": icon_url,
            "displayUrl": display_url,
            "brandName": brand_name,
            "description": description,
            "callToAction": call_to_action,
            "label": label,
            "imageCrop": image_crop,
            "trackerUrls": tracker_urls,
            "trackers": [
                {
                    "eventType": constants.TrackerEventType.get_name(tracker.get("event_type")),
                    "method": constants.TrackerMethod.get_name(tracker.get("method")),
                    "url": tracker.get("url"),
                    "fallbackUrl": tracker.get("fallback_url") or "",
                    "trackerOptional": tracker.get("tracker_optional"),
                }
                for tracker in trackers
            ]
            if trackers
            else None,
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
            icon_url=cad_db.get_icon_url(),
            display_url=cad_db.display_url,
            brand_name=cad_db.brand_name,
            description=cad_db.description,
            call_to_action=cad_db.call_to_action,
            label=cad_db.label,
            image_crop=cad_db.image_crop,
            tracker_urls=cad_db.tracker_urls,
            trackers=cad_db.trackers,
        )
        self.assertEqual(expected, cad)

    def test_contentads_list(self):
        magic_mixer.cycle(501).blend(core.models.ContentAd, ad_group=self.ad_group)
        r = self.client.get(reverse("restapi.contentad.v1:contentads_list"), data={"adGroupId": self.ad_group.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(500, len(resp_json["data"]))
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_contentads_list_approval_status(self):
        source = magic_mixer.blend(core.models.Source)
        content_ads = magic_mixer.cycle(4).blend(core.models.ContentAd, ad_group=self.ad_group)
        for content_ad in content_ads:
            magic_mixer.blend(core.models.ContentAdSource, content_ad=content_ad, source=source)

        r = self.client.get(
            reverse("restapi.contentad.v1:contentads_list"),
            data={"adGroupId": self.ad_group.id, "includeApprovalStatus": "true"},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(4, len(resp_json["data"]))
        for item in resp_json["data"]:
            self.assertTrue(item["approvalStatus"])

    def test_contentads_list_pagination(self):
        magic_mixer.cycle(10).blend(core.models.ContentAd, ad_group=self.ad_group)
        r = self.client.get(reverse("restapi.contentad.v1:contentads_list"), data={"adGroupId": self.ad_group.id})
        r_paginated = self.client.get(
            reverse("restapi.contentad.v1:contentads_list"), {"adGroupId": self.ad_group.id, "limit": 2, "offset": 5}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json["data"][5:7], resp_json_paginated["data"])

    def test_contentads_list_invalid_params(self):
        r = self.client.get(reverse("restapi.contentad.v1:contentads_list"), data={"adGroupId": "NON-NUMERIC"})
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual({"adGroupId": ["Invalid format"]}, resp_json["details"])

    def test_contentads_get(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        r = self.client.get(reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertNotIn("videoAssetId", resp_json["data"])

    def test_contentads_get_with_approval_status(self):
        source = magic_mixer.blend(core.models.Source)
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        magic_mixer.blend(core.models.ContentAdSource, content_ad=content_ad, source=source)
        r = self.client.get(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}),
            {"includeApprovalStatus": "true"},
        )
        resp_json = self.assertResponseValid(r)
        self.assertIn("approvalStatus", resp_json["data"])

    def test_contentads_get_with_image_width_and_image_height(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group, image_width=250, image_height=150)

        image_width = 450
        image_height = 350

        r = self.client.get(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}),
            {"imageWidth": image_width, "imageHeight": image_height},
        )
        resp_json = self.assertResponseValid(r)
        self.assertNotEqual(resp_json["data"]["imageUrl"], content_ad.get_image_url())
        self.assertEqual(resp_json["data"]["imageUrl"], content_ad.get_image_url(image_width, image_height))

        r = self.client.get(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}),
            {"imageWidth": image_width},
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"]["imageUrl"], content_ad.get_image_url())
        self.assertNotEqual(resp_json["data"]["imageUrl"], content_ad.get_image_url(image_width, image_height))

        r = self.client.get(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}),
            {"imageHeight": image_height},
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"]["imageUrl"], content_ad.get_image_url())
        self.assertNotEqual(resp_json["data"]["imageUrl"], content_ad.get_image_url(image_width, image_height))

        r = self.client.get(reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}))
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"]["imageUrl"], content_ad.get_image_url())
        self.assertNotEqual(resp_json["data"]["imageUrl"], content_ad.get_image_url(image_width, image_height))

    def test_contentads_get_video_ad(self):
        video_asset = magic_mixer.blend(core.features.videoassets.models.VideoAsset)
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        content_ad.video_asset = video_asset
        content_ad.save()
        content_ad.ad_group.campaign.type = dash.constants.CampaignType.VIDEO
        content_ad.ad_group.campaign.save(None)
        r = self.client.get(reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}))
        resp_json = self.assertResponseValid(r)
        self.assertEqual(str(video_asset.id), resp_json["data"]["videoAssetId"])

    def test_contentads_get_permissioned(self):
        utils.test_helper.add_permissions(self.user, ["can_use_ad_additional_data"])
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        r = self.client.get(reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}))
        resp_json = self.assertResponseValid(r)
        self.assertIn("additionalData", resp_json["data"])
        self.assertNotIn("type", resp_json["data"])
        self.assertNotIn("adTag", resp_json["data"])
        self.assertNotIn("adWidth", resp_json["data"])
        self.assertNotIn("adHeight", resp_json["data"])

    def test_contentads_get_permissioned_display(self):
        utils.test_helper.add_permissions(self.user, ["can_use_ad_additional_data"])
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        content_ad.ad_group.campaign.type = dash.constants.CampaignType.DISPLAY
        content_ad.ad_group.campaign.save(None)
        r = self.client.get(reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}))
        resp_json = self.assertResponseValid(r)
        self.assertIn("additionalData", resp_json["data"])
        self.assertIn("type", resp_json["data"])
        self.assertIn("adTag", resp_json["data"])
        self.assertIn("adWidth", resp_json["data"])
        self.assertIn("adHeight", resp_json["data"])

    def test_contentads_put(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        r = self.client.put(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}),
            data={"state": "INACTIVE", "label": "My new label"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["state"], "INACTIVE")
        self.assertEqual(resp_json["data"]["label"], "My new label")

    def test_contentads_put_permissioned(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        self.client.put(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.id}),
            data={"additionalData": {"a": 1}},
            format="json",
        )
        content_ad.refresh_from_db()
        self.assertEqual(content_ad.additional_data, None)

    def test_contentads_put_url(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        views.ACCOUNTS_CAN_EDIT_URL.append(content_ad.ad_group.campaign.account_id)
        r = self.client.put(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.pk}),
            data={"state": "INACTIVE", "url": "https://example.com"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["state"], "INACTIVE")
        self.assertEqual(resp_json["data"]["url"], "https://example.com")

    def test_contentads_put_updates(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        trackers = [
            {
                "eventType": constants.TrackerEventType.get_name(constants.TrackerEventType.IMPRESSION),
                "method": constants.TrackerMethod.get_name(constants.TrackerMethod.JS),
                "url": "https://t.test.com/tracker.js",
                "trackerOptional": False,
            }
        ]
        r = self.client.put(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.pk}),
            data={"trackerUrls": ["test1", "test2"], "trackers": trackers, "title": "newtitle"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["trackerUrls"], ["test1", "test2"])
        self.assertEqual(
            resp_json["data"]["trackers"],
            [
                {
                    "eventType": constants.TrackerEventType.get_name(constants.TrackerEventType.IMPRESSION),
                    "method": constants.TrackerMethod.get_name(constants.TrackerMethod.JS),
                    "url": "https://t.test.com/tracker.js",
                    "fallbackUrl": "",
                    "trackerOptional": False,
                }
            ],
        )
        self.assertNotEqual(resp_json["data"]["title"], "newtitle")  # readonly

    def test_contentads_put_brand_name_allowed(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        views.ACCOUNTS_CAN_EDIT_BRAND_NAME.append(content_ad.ad_group.campaign.account_id)
        r = self.client.put(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.pk}),
            data={"brandName": "New Brand Name"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["brandName"], "New Brand Name")

    def test_contentads_put_brand_name_not_allowed(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        old_brand_name = content_ad.brand_name
        views.ACCOUNTS_CAN_EDIT_BRAND_NAME = []
        r = self.client.put(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.pk}),
            data={"brandName": "New Brand Name"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(resp_json["data"]["brandName"], old_brand_name)

    def test_contentads_invalid_tracker(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)
        trackers = [
            {
                "eventType": constants.TrackerEventType.get_name(constants.TrackerEventType.VIEWABILITY),
                "method": constants.TrackerMethod.get_name(constants.TrackerMethod.JS),
                "url": "https://t.test.com/tracker.js",
                "trackerOptional": False,
            }
        ]
        r = self.client.put(
            reverse("restapi.contentad.v1:contentads_details", kwargs={"content_ad_id": content_ad.pk}),
            data={"trackers": trackers},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            [{"method": ["Javascript Tag method cannot be used together with Viewability type."]}],
            resp_json["details"]["trackers"],
        )


class TestBatchUpload(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        utils.test_helper.add_permissions(self.user, ["fea_can_change_campaign_type_to_display"])
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=self.account)

    @staticmethod
    def _mock_content_ad(title, state="ACTIVE"):
        return {
            "state": state,
            "url": "https://www.example.com/p/83895c0e-3bbe-4ad7-a0f6-c1917788ceb9",
            "title": title,
            "imageUrl": "http://example.com/p/srv/9018/e5d6adb68f1d404f82541e335c50bbd3.jpg?w=1024&h=768&fit=crop&crop=center&fm=jpg",
            "iconUrl": "http://example.com/p/srv/9018/e5d6adb68f1d404f82541e335c50bbd4.jpg?w=300&h=300&fit=crop&crop=center&fm=jpg",
            "displayUrl": "kuhic.com",
            "brandName": "Kassulke-Hartmann",
            "description": "People really should avert their gaze from the modern survival thinking for just a bit and also look at how folks 150 years ago did it.",
            "callToAction": "Watch More",
            "label": "",
            "imageCrop": "center",
            "trackerUrls": ["https://www.example.com/a", "https://www.example.com/b"],
            "trackers": [
                {
                    "eventType": constants.TrackerEventType.get_name(constants.TrackerEventType.IMPRESSION),
                    "method": constants.TrackerMethod.get_name(constants.TrackerMethod.JS),
                    "url": "https://t.test.com/tracker.js",
                    "trackerOptional": False,
                }
            ],
        }

    @staticmethod
    def _mock_image_ad(title):
        return {
            "state": "ACTIVE",
            "url": "https://www.example.com/p/83895c0e-3bbe-4ad7-a0f6-c1917788ceb9",
            "title": title,
            "imageUrl": "http://example.com/p/srv/9018/e5d6adb68f1d404f82541e335c50bbd3.jpg?w=1024&h=768&fit=crop&crop=center&fm=jpg",
            "label": "",
            "displayUrl": "kuhic.com",
            "trackerUrls": ["https://www.example.com/a", "https://www.example.com/b"],
            "trackers": [
                {
                    "eventType": constants.TrackerEventType.get_name(constants.TrackerEventType.IMPRESSION),
                    "method": constants.TrackerMethod.get_name(constants.TrackerMethod.JS),
                    "url": "https://t.test.com/tracker.js",
                    "trackerOptional": False,
                }
            ],
            "type": constants.AdType.get_name(constants.AdType.IMAGE),
        }

    @staticmethod
    def _mock_ad_tag(title):
        return {
            "state": "ACTIVE",
            "url": "https://www.example.com/p/83895c0e-3bbe-4ad7-a0f6-c1917788ceb9",
            "title": title,
            "label": "",
            "ad_tag": "<body></body>",
            "adWidth": 300,
            "adHeight": 250,
            "displayUrl": "kuhic.com",
            "trackerUrls": ["https://www.example.com/a", "https://www.example.com/b"],
            "trackers": [
                {
                    "eventType": constants.TrackerEventType.get_name(constants.TrackerEventType.IMPRESSION),
                    "method": constants.TrackerMethod.get_name(constants.TrackerMethod.JS),
                    "url": "https://t.test.com/tracker.js",
                    "trackerOptional": False,
                }
            ],
            "type": constants.AdType.get_name(constants.AdType.AD_TAG),
        }

    @staticmethod
    def _approve_candidates(batch, is_display_ad=False):
        for i, candidate in enumerate(batch.contentadcandidate_set.all()):
            candidate.image_id = "p/srv/8678/13f72b5e37a64860a73ac95ff51b2a3e"
            candidate.image_hash = "1234"
            candidate.image_height = 250 if is_display_ad else 500
            candidate.image_width = 300 if is_display_ad else 500
            candidate.image_file_size = 120000
            candidate.icon_id = "p/srv/8678/13f72b5e37a64860a73ac95ff51b2a3f{}".format(str(i))
            candidate.icon_hash = "2345"
            candidate.icon_height = 300
            candidate.icon_width = 300
            candidate.icon_file_size = 100000
            candidate.image_status = constants.AsyncUploadJobStatus.OK
            candidate.icon_status = constants.AsyncUploadJobStatus.OK
            candidate.url_status = constants.AsyncUploadJobStatus.OK
            candidate.save()
        contentupload.upload._handle_auto_save(batch)

    @mock.patch("dash.features.contentupload.upload.invoke_external_validation", mock.Mock())
    def test_content_batch_upload_success(self):
        ad1 = self._mock_content_ad("test1")
        ad2 = self._mock_content_ad("test2")
        paused_ad = self._mock_content_ad("test3", "INACTIVE")
        del ad2["iconUrl"]
        to_upload = [ad1, ad2, paused_ad]
        r = self.client.post(
            reverse("restapi.contentad.v1:contentads_batch_list") + "?adGroupId={}".format(self.ad_group.id),
            data=to_upload,
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertIn("id", resp_json["data"])

        batch_id = int(resp_json["data"]["id"])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        self._approve_candidates(batch)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
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
            self.assertEqual(
                [
                    {
                        "eventType": constants.TrackerEventType.get_name(constants.TrackerEventType.IMPRESSION),
                        "method": constants.TrackerMethod.get_name(constants.TrackerMethod.JS),
                        "url": "https://t.test.com/tracker.js",
                        "fallbackUrl": "",
                        "trackerOptional": False,
                    }
                ],
                resp_json["data"]["approvedContentAds"][i]["trackers"],
            )

    @mock.patch("dash.features.contentupload.upload.invoke_external_validation", mock.Mock())
    def test_video_batch_upload_success(self):
        self.ad_group.campaign.type = dash.constants.CampaignType.VIDEO
        self.ad_group.campaign.save(None)
        video_asset_1 = magic_mixer.blend(core.features.videoassets.models.VideoAsset, account=self.account)
        video_asset_2 = magic_mixer.blend(core.features.videoassets.models.VideoAsset, account=self.account)
        ad1 = self._mock_content_ad("test1")
        ad2 = self._mock_content_ad("test2")
        ad1.update({"videoAssetId": str(video_asset_1.id)})
        ad2.update({"videoAssetId": str(video_asset_2.id)})
        to_upload = [ad1, ad2]

        r = self.client.post(
            reverse("restapi.contentad.v1:contentads_batch_list") + "?adGroupId={}".format(self.ad_group.id),
            to_upload,
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertIn("id", resp_json["data"])

        batch_id = int(resp_json["data"]["id"])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        self._approve_candidates(batch)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "DONE")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        saved_video_ads = batch.contentad_set.all().order_by("pk")
        self.assertEqual(len(to_upload), len(resp_json["data"]["approvedContentAds"]))
        self.assertEqual(len(to_upload), len(saved_video_ads))
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
                "videoAssetId",
            ):
                self.assertEqual(to_upload[i][field], resp_json["data"]["approvedContentAds"][i][field])
            self.assertEqual(saved_video_ads[i].id, int(resp_json["data"]["approvedContentAds"][i]["id"]))
            self.assertEqual(
                [
                    {
                        "eventType": constants.TrackerEventType.get_name(constants.TrackerEventType.IMPRESSION),
                        "method": constants.TrackerMethod.get_name(constants.TrackerMethod.JS),
                        "url": "https://t.test.com/tracker.js",
                        "fallbackUrl": "",
                        "trackerOptional": False,
                    }
                ],
                resp_json["data"]["approvedContentAds"][i]["trackers"],
            )

    def test_display_batch_upload_success(self):
        self.ad_group.campaign.type = dash.constants.CampaignType.DISPLAY
        self.ad_group.campaign.save(None)
        to_upload = [self._mock_image_ad("image"), self._mock_ad_tag("ad_tag")]
        r = self.client.post(
            reverse("restapi.contentad.v1:contentads_batch_list") + "?adGroupId={}".format(self.ad_group.id),
            to_upload,
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertIn("id", resp_json["data"])

        batch_id = int(resp_json["data"]["id"])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        self._approve_candidates(batch, is_display_ad=True)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "DONE")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        saved_display_ads = batch.contentad_set.all().order_by("pk")
        self.assertEqual(len(to_upload), len(resp_json["data"]["approvedContentAds"]))
        self.assertEqual(len(to_upload), len(saved_display_ads))
        for i in range(len(to_upload)):
            for field in ("state", "title", "displayUrl", "label", "trackerUrls"):
                self.assertEqual(to_upload[i][field], resp_json["data"]["approvedContentAds"][i][field])
            self.assertEqual(saved_display_ads[i].id, int(resp_json["data"]["approvedContentAds"][i]["id"]))
            self.assertEqual(
                [
                    {
                        "eventType": constants.TrackerEventType.get_name(constants.TrackerEventType.IMPRESSION),
                        "method": constants.TrackerMethod.get_name(constants.TrackerMethod.JS),
                        "url": "https://t.test.com/tracker.js",
                        "fallbackUrl": "",
                        "trackerOptional": False,
                    }
                ],
                resp_json["data"]["approvedContentAds"][i]["trackers"],
            )

    def test_display_batch_upload_ad_group_archived(self):
        self.ad_group.archived = True
        self.ad_group.save(None)
        to_upload = [self._mock_content_ad("test1"), self._mock_content_ad("test2")]
        resp = self.client.post(
            reverse("restapi.contentad.v1:contentads_batch_list") + "?adGroupId={}".format(self.ad_group.id),
            to_upload,
            format="json",
        )
        self.assertEqual(400, resp.status_code)
        self.assertEqual("Can not create a content ad on an archived ad group.", json.loads(resp.content)["details"])

    @staticmethod
    def _reject_candidates(batch):
        for candidate in batch.contentadcandidate_set.all():
            candidate.image_status = constants.AsyncUploadJobStatus.FAILED
            candidate.icon_status = constants.AsyncUploadJobStatus.FAILED
            candidate.url_status = constants.AsyncUploadJobStatus.FAILED
            candidate.save()
        contentupload.upload._handle_auto_save(batch)

    @mock.patch("dash.features.contentupload.upload.invoke_external_validation", mock.Mock())
    def test_content_batch_upload_failure(self):
        to_upload = [self._mock_content_ad("test1"), self._mock_content_ad("test2")]
        r = self.client.post(
            reverse("restapi.contentad.v1:contentads_batch_list") + "?adGroupId={}".format(self.ad_group.id),
            to_upload,
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertIn("id", resp_json["data"])

        batch_id = int(resp_json["data"]["id"])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        self._reject_candidates(batch)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "FAILED")
        self.assertEqual(resp_json["data"]["approvedContentAds"], [])
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

    @mock.patch("dash.features.contentupload.upload.invoke_external_validation", mock.Mock())
    def test_video_batch_upload_failure(self):
        self.ad_group.campaign.type = dash.constants.CampaignType.VIDEO
        self.ad_group.campaign.save(None)

        to_upload = [self._mock_content_ad("test1"), self._mock_content_ad("test2")]
        r = self.client.post(
            reverse("restapi.contentad.v1:contentads_batch_list") + "?adGroupId={}".format(self.ad_group.id),
            to_upload,
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertIn("id", resp_json["data"])
        for status in resp_json["data"]["validationStatus"]:
            self.assertEqual(status["videoAssetId"], ["Video asset required on video campaigns"])

        batch_id = int(resp_json["data"]["id"])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        self._approve_candidates(batch)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "FAILED")
        self.assertEqual(resp_json["data"]["approvedContentAds"], [])
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))
        for status in resp_json["data"]["validationStatus"]:
            self.assertEqual(status["videoAssetId"], ["Video asset required on video campaigns"])

    @mock.patch("dash.features.contentupload.upload.invoke_external_validation", mock.Mock())
    def test_display_batch_upload_failure(self):
        to_upload = [self._mock_image_ad("image"), self._mock_ad_tag("ad_tag")]
        r = self.client.post(
            reverse("restapi.contentad.v1:contentads_batch_list") + "?adGroupId={}".format(self.ad_group.id),
            to_upload,
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertIn("id", resp_json["data"])

        batch_id = int(resp_json["data"]["id"])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))

        self._reject_candidates(batch)

        r = self.client.get(reverse("restapi.contentad.v1:contentads_batch_details", kwargs={"batch_id": batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "FAILED")
        self.assertEqual(resp_json["data"]["approvedContentAds"], [])
        self.assertEqual(batch_id, int(resp_json["data"]["id"]))
