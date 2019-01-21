# -*- coding: utf-8 -*-
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from mock import MagicMock
from mock import patch

from dash import constants
from dash import models
from utils.magic_mixer import magic_mixer
from zemauth.models import User


def _get_client(superuser=False):
    password = "secret"

    user_id = 1 if superuser else 2
    user = User.objects.get(pk=user_id)
    username = user.email

    client = Client()
    client.login(username=username, password=password)

    return client


class UploadCsvTestCase(TestCase):

    fixtures = ["test_upload.yaml"]

    @patch("utils.lambda_helper.invoke_lambda", MagicMock())
    def test_post_content_ad(self):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            "test_upload.csv",
            b"URL,Title,Image URL,Label,Image Crop,Primary impression tracker url,Secondary impression tracker url,Brand name,Display URL,"
            b"Call to Action,Description\nhttp://zemanta.com/test-content-ad,test content ad,"
            b"http://zemanta.com/test-image.jpg,test,entropy,https://t.zemanta.com/px1.png,"
            b"https://t.zemanta.com/px2.png,Zemanta,zemanta.com,Click for more,description",
        )
        response = _get_client().post(
            reverse("upload_csv", kwargs={}),
            {"candidates": mock_file, "batch_name": "batch 1", "ad_group_id": 1, "account_id": 1},
            follow=True,
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {"__all__": ["Content ad still processing"]}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "success": True,
                "data": {"batch_id": batch.id, "batch_name": "batch 1", "candidates": [expected_candidate]},
            },
            json.loads(response.content),
        )

        self.assertEqual("batch 1", batch.name)
        self.assertEqual("test_upload.csv", batch.original_filename)

        self.assertEqual("test", candidate.label)
        self.assertEqual("http://zemanta.com/test-content-ad", candidate.url)
        self.assertEqual("test content ad", candidate.title)
        self.assertEqual("http://zemanta.com/test-image.jpg", candidate.image_url)
        self.assertEqual("entropy", candidate.image_crop)
        self.assertEqual("https://t.zemanta.com/px1.png", candidate.primary_tracker_url)
        self.assertEqual("https://t.zemanta.com/px2.png", candidate.secondary_tracker_url)
        self.assertEqual("zemanta.com", candidate.display_url)
        self.assertEqual("Zemanta", candidate.brand_name)
        self.assertEqual("description", candidate.description)
        self.assertEqual("Click for more", candidate.call_to_action)

    @patch("utils.lambda_helper.invoke_lambda", MagicMock())
    def test_post_image_ad(self):
        user = User.objects.get(pk=2)
        account = magic_mixer.blend(models.Account, users=[user])
        campaign = magic_mixer.blend(models.Campaign, account=account, type=constants.CampaignType.DISPLAY)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        mock_file = SimpleUploadedFile(
            "test_upload.csv",
            b"URL,Name,Image URL,Label,Primary impression tracker url,Secondary impression tracker url\n"
            b"http://zemanta.com/test-content-ad,test content ad,"
            b"http://zemanta.com/test-image.jpg,test,https://t.zemanta.com/px1.png,"
            b"https://t.zemanta.com/px2.png",
        )
        response = _get_client().post(
            reverse("upload_csv", kwargs={}),
            {"candidates": mock_file, "batch_name": "batch 12", "ad_group_id": ad_group.id, "account_id": account.id},
            follow=True,
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group.id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {"__all__": ["Content ad still processing"]}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "success": True,
                "data": {"batch_id": batch.id, "batch_name": "batch 12", "candidates": [expected_candidate]},
            },
            json.loads(response.content),
        )

        self.assertEqual("batch 12", batch.name)
        self.assertEqual("test_upload.csv", batch.original_filename)

        self.assertEqual(constants.AdType.IMAGE, candidate.type)
        self.assertEqual("test", candidate.label)
        self.assertEqual("http://zemanta.com/test-content-ad", candidate.url)
        self.assertEqual("test content ad", candidate.title)
        self.assertEqual("http://zemanta.com/test-image.jpg", candidate.image_url)
        self.assertEqual("center", candidate.image_crop)
        self.assertEqual("https://t.zemanta.com/px1.png", candidate.primary_tracker_url)
        self.assertEqual("https://t.zemanta.com/px2.png", candidate.secondary_tracker_url)
        self.assertEqual("", candidate.display_url)
        self.assertEqual("", candidate.brand_name)
        self.assertEqual("", candidate.description)
        self.assertEqual("Read more", candidate.call_to_action)

    @patch("utils.lambda_helper.invoke_lambda", MagicMock())
    def test_post_ad_tag(self):
        user = User.objects.get(pk=2)
        account = magic_mixer.blend(models.Account, users=[user])
        campaign = magic_mixer.blend(models.Campaign, account=account, type=constants.CampaignType.DISPLAY)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        mock_file = SimpleUploadedFile(
            "test_upload.csv",
            b"URL,Name,Image URL,Creative Size,Ad Tag,Label,Primary impression tracker url,Secondary impression tracker url\n"
            b"http://zemanta.com/test-content-ad,test content ad,"
            b",  300 X  250 ,<body></body>,test,https://t.zemanta.com/px1.png,"
            b"https://t.zemanta.com/px2.png",
        )
        response = _get_client().post(
            reverse("upload_csv", kwargs={}),
            {"candidates": mock_file, "batch_name": "batch 12", "ad_group_id": ad_group.id, "account_id": account.id},
            follow=True,
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group.id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {"__all__": ["Content ad still processing"]}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "success": True,
                "data": {"batch_id": batch.id, "batch_name": "batch 12", "candidates": [expected_candidate]},
            },
            json.loads(response.content),
        )

        self.assertEqual("batch 12", batch.name)
        self.assertEqual("test_upload.csv", batch.original_filename)

        self.assertEqual(constants.AdType.AD_TAG, candidate.type)
        self.assertEqual("test", candidate.label)
        self.assertEqual("http://zemanta.com/test-content-ad", candidate.url)
        self.assertEqual("test content ad", candidate.title)
        self.assertEqual("<body></body>", candidate.ad_tag)
        self.assertEqual(300, candidate.image_width)
        self.assertEqual(250, candidate.image_height)
        self.assertEqual("", candidate.image_url)
        self.assertEqual("center", candidate.image_crop)
        self.assertEqual("https://t.zemanta.com/px1.png", candidate.primary_tracker_url)
        self.assertEqual("https://t.zemanta.com/px2.png", candidate.secondary_tracker_url)
        self.assertEqual("", candidate.display_url)
        self.assertEqual("", candidate.brand_name)
        self.assertEqual("", candidate.description)
        self.assertEqual("Read more", candidate.call_to_action)

    @patch("utils.lambda_helper.invoke_lambda", MagicMock())
    def test_post_content_ad_defaults(self):
        ad_group_id = 1
        ad_group_settings = models.AdGroup.objects.get(id=ad_group_id).get_current_settings().copy_settings()
        ad_group_settings.brand_name = "Default brand name"
        ad_group_settings.save(None)

        mock_file = SimpleUploadedFile(
            "test_upload.csv",
            b"URL,Title,Image URL,Label,Image Crop,Primary impression tracker url,"
            b"Secondary impression tracker url,Description,Display URL,brand name\nhttp://example.com/test-content-ad,"
            b"test content ad,http://zemanta.com/test-image.jpg,test,entropy,https://t.zemanta.com/px1.png,"
            b"https://t.zemanta.com/px2.png,description,example.com,Example",
        )
        response = _get_client().post(
            reverse("upload_csv", kwargs={}),
            {"candidates": mock_file, "batch_name": "batch 1", "ad_group_id": ad_group_id, "account_id": 1},
            follow=True,
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {"__all__": ["Content ad still processing"]}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "success": True,
                "data": {"batch_id": batch.id, "batch_name": "batch 1", "candidates": [expected_candidate]},
            },
            json.loads(response.content),
        )

        self.assertEqual("batch 1", batch.name)
        self.assertEqual("test_upload.csv", batch.original_filename)

        self.assertEqual("test", candidate.label)
        self.assertEqual("http://example.com/test-content-ad", candidate.url)
        self.assertEqual("test content ad", candidate.title)
        self.assertEqual("http://zemanta.com/test-image.jpg", candidate.image_url)
        self.assertEqual("entropy", candidate.image_crop)
        self.assertEqual("https://t.zemanta.com/px1.png", candidate.primary_tracker_url)
        self.assertEqual("https://t.zemanta.com/px2.png", candidate.secondary_tracker_url)
        self.assertEqual("example.com", candidate.display_url)
        self.assertEqual("Example", candidate.brand_name)
        self.assertEqual("description", candidate.description)
        self.assertEqual("Read more", candidate.call_to_action)

    @patch("utils.lambda_helper.invoke_lambda", MagicMock())
    def test_post_content_ad_errors(self):
        ad_group_id = 1
        mock_file = SimpleUploadedFile(
            "test_upload.csv",
            b"URL,Title,Image URL,Label,Image Crop,Primary impression tracker url,Secondary impression tracker url\n"
            b"ahttp://zemanta.com/test-content-ad,test content ad,ahttp://zemanta.com/test-image.jpg,"
            b"testtoolonglabelforthecontentadcandidatelabelfield,entropy,"
            b"http://t.zemanta.com/px1.png,https://t.zemanta.com/px2.png",
        )
        response = _get_client().post(
            reverse("upload_csv", kwargs={}),
            {"candidates": mock_file, "batch_name": "batch 1", "ad_group_id": ad_group_id, "account_id": 1},
            follow=True,
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group_id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {
            "__all__": ["Content ad still processing"],
            "description": ["Missing description"],
            "primary_tracker_url": ["Impression tracker URLs have to be HTTPS"],
            "image_url": ["Invalid image URL"],
            "display_url": ["Missing display URL"],
            "url": ["Invalid URL"],
            "brand_name": ["Missing brand name"],
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "success": True,
                "data": {"batch_id": batch.id, "batch_name": "batch 1", "candidates": [expected_candidate]},
            },
            json.loads(response.content),
        )

    @patch("utils.lambda_helper.invoke_lambda", MagicMock())
    def test_post_image_ad_errors(self):
        user = User.objects.get(pk=2)
        account = magic_mixer.blend(models.Account, users=[user])
        campaign = magic_mixer.blend(models.Campaign, account=account, type=constants.CampaignType.DISPLAY)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        mock_file = SimpleUploadedFile(
            "test_upload.csv",
            b"URL,Name,Image URL,Label,Primary impression tracker url,Secondary impression tracker url\n"
            b"ahttp://zemanta.com/test-content-ad,,"
            b"ahttp://zemanta.com/test-image.jpg,,http://t.zemanta.com/px1.png,"
            b"https://t.zemanta.com/px2.png",
        )
        response = _get_client().post(
            reverse("upload_csv", kwargs={}),
            {"candidates": mock_file, "batch_name": "batch 12", "ad_group_id": ad_group.id, "account_id": account.id},
            follow=True,
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group.id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {
            "__all__": ["Content ad still processing"],
            "primary_tracker_url": ["Impression tracker URLs have to be HTTPS"],
            "image_url": ["Invalid image URL"],
            "title": ["Missing ad name"],
            "url": ["Invalid URL"],
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "success": True,
                "data": {"batch_id": batch.id, "batch_name": "batch 12", "candidates": [expected_candidate]},
            },
            json.loads(response.content),
        )

    @patch("utils.lambda_helper.invoke_lambda", MagicMock())
    def test_post_ad_tag_errors(self):
        user = User.objects.get(pk=2)
        account = magic_mixer.blend(models.Account, users=[user])
        campaign = magic_mixer.blend(models.Campaign, account=account, type=constants.CampaignType.DISPLAY)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        mock_file = SimpleUploadedFile(
            "test_upload.csv",
            b"URL,Name,Image URL,Creative Size,Ad Tag,Label,Primary impression tracker url,Secondary impression tracker url\n"
            b"ahttp://zemanta.com/test-content-ad,,"
            b",  350 X  200 ,<body></body>,test,http://t.zemanta.com/px1.png,"
            b"https://t.zemanta.com/px2.png",
        )
        response = _get_client().post(
            reverse("upload_csv", kwargs={}),
            {"candidates": mock_file, "batch_name": "batch 12", "ad_group_id": ad_group.id, "account_id": account.id},
            follow=True,
        )

        batch = models.UploadBatch.objects.filter(ad_group_id=ad_group.id).latest()
        candidate = batch.contentadcandidate_set.get()

        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {
            "__all__": ["Content ad still processing"],
            "primary_tracker_url": ["Impression tracker URLs have to be HTTPS"],
            "title": ["Missing ad name"],
            "url": ["Invalid URL"],
            "image_url": ["Image size invalid. Supported sizes are (width x height): 300x250, 320x50"],
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "success": True,
                "data": {"batch_id": batch.id, "batch_name": "batch 12", "candidates": [expected_candidate]},
            },
            json.loads(response.content),
        )


class UploadStatusTestCase(TestCase):

    fixtures = ["test_upload.yaml"]

    def test_pending(self):
        batch_id = 1
        ad_group_id = 2

        candidate = models.ContentAdCandidate.objects.get(ad_group_id=ad_group_id)
        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {"__all__": ["Content ad still processing"]}

        response = _get_client().get(reverse("upload_status", kwargs={"batch_id": batch_id}), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"success": True, "data": {"candidates": {str(candidate.id): expected_candidate}}},
            json.loads(response.content),
        )

    def test_ok(self):
        batch_id = 8
        ad_group_id = 7

        candidate = models.ContentAdCandidate.objects.get(ad_group_id=ad_group_id)
        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {}

        response = _get_client().get(reverse("upload_status", kwargs={"batch_id": batch_id}), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"success": True, "data": {"candidates": {str(candidate.id): expected_candidate}}},
            json.loads(response.content),
        )

    def test_failed(self):
        batch_id = 3
        ad_group_id = 4

        candidate = models.ContentAdCandidate.objects.get(ad_group_id=ad_group_id, batch_id=batch_id)
        expected_candidate = candidate.to_dict()
        expected_candidate["errors"] = {"image_url": ["Image could not be processed"], "url": ["Content unreachable"]}

        response = _get_client().get(reverse("upload_status", kwargs={"batch_id": batch_id}), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {"success": True, "data": {"candidates": {str(candidate.id): expected_candidate}}},
            json.loads(response.content),
        )


class UploadSaveTestCase(TestCase):

    fixtures = ["test_upload.yaml"]

    @staticmethod
    def _mock_insert_redirects(content_ads, clickthrough_resolve):
        return {
            str(content_ad.id): {"redirect": {"url": "http://example.com"}, "redirectid": "abc123"}
            for content_ad in content_ads
        }

    @patch("utils.sspd_client.sync_batch", MagicMock())
    @patch("utils.redirector_helper.insert_redirects")
    def test_ok(self, mock_insert_batch):
        mock_insert_batch.side_effect = self._mock_insert_redirects
        batch_id = 8
        ad_group_id = 7
        models.ContentAdCandidate.objects.filter(id=7).update(type=constants.AdType.VIDEO)

        response = _get_client().post(
            reverse("upload_save", kwargs={"batch_id": batch_id}),
            json.dumps({}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({"success": True, "data": {"num_successful": 1}}, json.loads(response.content))
        self.assertEqual(
            models.History.objects.filter(ad_group=ad_group_id, level=constants.HistoryLevel.AD_GROUP)
            .latest("created_dt")
            .changes_text,
            'Imported batch "batch 2" with 1 content ad.',
        )

    @patch("utils.redirector_helper.insert_redirects")
    def test_type_mismatch(self, mock_insert_batch):
        mock_insert_batch.side_effect = self._mock_insert_redirects
        batch_id = 8

        response = _get_client().post(
            reverse("upload_save", kwargs={"batch_id": batch_id}),
            json.dumps({}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            {
                "success": False,
                "data": {
                    "error_code": "ValidationError",
                    "message": "Creative type does not match the campaign type.",
                    "errors": None,
                    "data": None,
                },
            },
            json.loads(response.content),
        )

    @patch("utils.sspd_client.sync_batch", MagicMock())
    @patch("utils.redirector_helper.insert_redirects")
    def test_change_batch_name(self, mock_insert_batch):
        mock_insert_batch.side_effect = self._mock_insert_redirects

        batch_id = 8
        models.ContentAdCandidate.objects.filter(id=7).update(type=constants.AdType.VIDEO)

        response = _get_client().post(
            reverse("upload_save", kwargs={"batch_id": batch_id}),
            json.dumps({"batch_name": "new batch name"}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({"success": True, "data": {"num_successful": 1}}, json.loads(response.content))

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(batch.name, "new batch name")

    def test_invalid_batch_name(self):
        batch_id = 2

        response = _get_client().post(
            reverse("upload_save", kwargs={"batch_id": batch_id}),
            json.dumps({"batch_name": "new batch name" * 50}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            {
                "success": False,
                "data": {
                    "data": None,
                    "error_code": "ValidationError",
                    "errors": {"batch_name": ["Batch name is too long (700/255)."]},
                    "message": None,
                },
            },
            json.loads(response.content),
        )

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(batch.name, "batch 2")

    @patch("utils.redirector_helper.insert_redirects")
    def test_errors(self, mock_insert_batch):
        mock_insert_batch.side_effect = self._mock_insert_redirects

        batch_id = 3

        response = _get_client().post(
            reverse("upload_save", kwargs={"batch_id": batch_id}),
            json.dumps({}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(
            {
                "success": False,
                "data": {
                    "data": None,
                    "error_code": "ValidationError",
                    "errors": None,
                    "message": "Save not permitted - candidate errors exist",
                },
            },
            json.loads(response.content),
        )
        self.assertEqual(400, response.status_code)

    @patch("utils.redirector_helper.insert_redirects")
    def test_redirector_error(self, mock_insert_batch):
        mock_insert_batch.side_effect = Exception()

        batch_id = 8
        ad_group_id = 7
        models.ContentAdCandidate.objects.filter(id=7).update(type=constants.AdType.VIDEO)

        response = _get_client().post(
            reverse("upload_save", kwargs={"batch_id": batch_id}),
            json.dumps({}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(500, response.status_code)
        self.assertEqual(
            {"success": False, "data": {"error_code": "ServerError", "message": "An error occurred."}},
            json.loads(response.content),
        )
        self.assertEqual(0, models.ContentAd.objects.filter(ad_group_id=ad_group_id).count())

    def test_invalid_batch_status(self):
        batch_id = 4

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

        response = _get_client().post(
            reverse("upload_save", kwargs={"batch_id": batch_id}),
            json.dumps({}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            {
                "success": False,
                "data": {
                    "data": None,
                    "error_code": "ValidationError",
                    "errors": None,
                    "message": "Invalid batch status",
                },
            },
            json.loads(response.content),
        )

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

    def test_invalid_batch_id(self):
        ad_group = magic_mixer.blend(models.AdGroup)
        account = ad_group.campaign.account
        batch = magic_mixer.blend(models.UploadBatch, ad_group=ad_group, account=account)

        response = _get_client().post(
            reverse("upload_save", kwargs={"batch_id": batch.id}),
            json.dumps({}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            {"success": False, "data": {"error_code": "MissingDataError", "message": "Upload batch does not exist"}},
            json.loads(response.content),
        )

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)


class CandidatesDownloadTestCase(TestCase):

    fixtures = ["test_upload.yaml"]

    def test_valid(self):
        batch_id = 1

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client().get(reverse("upload_candidates_download", kwargs={"batch_id": batch_id}), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            (
                '"URL","Title","Image URL","Display URL","Brand name","Description","Call to action",'
                '"Label","Image crop","Primary impression tracker URL","Secondary impression'
                ' tracker URL"\r\n"http://zemanta.com/blog","Zemanta blog čšž",'
                '"http://zemanta.com/img.jpg","zemanta.com","Zemanta","Zemanta blog","Read more",'
                '"content ad 1","entropy","",""\r\n'
            ).encode("utf-8"),
            response.content,
        )
        self.assertEqual('attachment; filename="batch 1.csv"', response.get("Content-Disposition"))

    def test_valid_display(self):
        batch_id = 1

        batch = models.UploadBatch.objects.get(id=batch_id)
        batch.ad_group.campaign.type = constants.CampaignType.DISPLAY
        batch.ad_group.campaign.save(None)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client().get(reverse("upload_candidates_download", kwargs={"batch_id": batch_id}), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            (
                '"URL","Title","Image URL","Display URL","Brand name","Description","Call to action",'
                '"Label","Image crop","Primary impression tracker URL","Secondary impression'
                ' tracker URL","Creative size","Ad tag"\r\n"http://zemanta.com/blog","Zemanta blog čšž",'
                '"http://zemanta.com/img.jpg","zemanta.com","Zemanta","Zemanta blog","Read more",'
                '"content ad 1","entropy","","","",""\r\n'
            ).encode("utf-8"),
            response.content,
        )
        self.assertEqual('attachment; filename="batch 1.csv"', response.get("Content-Disposition"))

    def test_custom_batch_name(self):
        batch_id = 1

        response = _get_client().get(
            reverse("upload_candidates_download", kwargs={"batch_id": batch_id}),
            {"batch_name": "Another batch"},
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual('attachment; filename="Another batch.csv"', response.get("Content-Disposition"))

    def test_wrong_batch_id(self):
        ad_group = magic_mixer.blend(models.AdGroup)
        account = ad_group.campaign.account
        batch = magic_mixer.blend(models.UploadBatch, ad_group=ad_group, account=account)

        response = _get_client().get(reverse("upload_candidates_download", kwargs={"batch_id": batch.id}), follow=True)
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            {"success": False, "data": {"error_code": "MissingDataError", "message": "Upload batch does not exist"}},
            json.loads(response.content),
        )

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)


class UploadCancelTestCase(TestCase):

    fixtures = ["test_upload.yaml"]

    def test_valid(self):
        batch_id = 1

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        response = _get_client().post(reverse("upload_cancel", kwargs={"batch_id": batch_id}), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual({"success": True}, json.loads(response.content))

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.CANCELLED, batch.status)

    def test_invalid(self):
        batch_id = 1

        batch = models.UploadBatch.objects.get(id=batch_id)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

        batch.status = constants.UploadBatchStatus.DONE
        batch.save()

        response = _get_client().post(reverse("upload_cancel", kwargs={"batch_id": batch_id}), follow=True)
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            {
                "success": False,
                "data": {
                    "data": None,
                    "error_code": "ValidationError",
                    "errors": {"cancel": "Cancel action unsupported at this stage"},
                    "message": None,
                },
            },
            json.loads(response.content),
        )

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

    def test_wrong_batch_id(self):
        ad_group = magic_mixer.blend(models.AdGroup)
        account = ad_group.campaign.account
        batch = magic_mixer.blend(models.UploadBatch, ad_group=ad_group, account=account)

        response = _get_client().post(reverse("upload_cancel", kwargs={"batch_id": batch.id}), follow=True)
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            {"success": False, "data": {"error_code": "MissingDataError", "message": "Upload batch does not exist"}},
            json.loads(response.content),
        )

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)


class UploadBatchTest(TestCase):

    fixtures = ["test_upload.yaml"]

    def test_create_empty_batch(self):
        batch_name = "test"

        response = _get_client().post(
            reverse("upload_batch", kwargs={}),
            json.dumps({"batch_name": batch_name, "account_id": 1, "ad_group_id": 1}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        batch = models.UploadBatch.objects.latest("created_dt")
        new_candidate = batch.contentadcandidate_set.get()

        response = json.loads(response.content)
        self.assertEqual(
            {
                "data": {"batch_id": batch.id, "batch_name": batch_name, "candidates": [new_candidate.to_dict()]},
                "success": True,
            },
            response,
        )

    def test_create_empty_batch_invalid_batch_name(self):
        batch_name = ""

        response = _get_client().post(
            reverse("upload_batch", kwargs={}),
            json.dumps({"batch_name": batch_name}),
            content_type="application/json",
            follow=True,
        )
        self.assertEqual(400, response.status_code)


class CandidateTest(TestCase):

    fixtures = ["test_upload.yaml"]

    def test_get_candidate(self):
        batch_id = 1
        candidate_id = 1

        response = _get_client().get(
            reverse("upload_candidate", kwargs={"batch_id": batch_id, "candidate_id": candidate_id}), follow=True
        )
        self.assertEqual(400, response.status_code)

    def test_get_candidate_list(self):
        batch_id = 1
        self.maxDiff = None

        response = _get_client().get(reverse("upload_candidate", kwargs={"batch_id": batch_id}), follow=True)
        self.assertEqual(200, response.status_code)

        response = json.loads(response.content)
        self.assertEqual(
            {
                "data": {
                    "candidates": [
                        {
                            "id": 1,
                            "label": "content ad 1",
                            "url": "http://zemanta.com/blog",
                            "title": "Zemanta blog čšž",
                            "type": constants.AdType.CONTENT,
                            "image_url": "http://zemanta.com/img.jpg",
                            "image_crop": "entropy",
                            "display_url": "zemanta.com",
                            "brand_name": "Zemanta",
                            "description": "Zemanta blog",
                            "call_to_action": "Read more",
                            "errors": {"__all__": ["Content ad still processing"]},
                            "hosted_image_url": None,
                            "image_height": None,
                            "image_width": None,
                            "image_id": None,
                            "image_hash": None,
                            "image_file_size": None,
                            "image_status": constants.AsyncUploadJobStatus.PENDING_START,
                            "url_status": constants.AsyncUploadJobStatus.PENDING_START,
                            "primary_tracker_url": None,
                            "secondary_tracker_url": None,
                            "video_asset_id": None,
                            "ad_tag": None,
                            "additional_data": None,
                        }
                    ]
                },
                "success": True,
            },
            response,
        )

    def test_add_candidate(self):
        batch_id = 1

        response = _get_client().post(reverse("upload_candidate", kwargs={"batch_id": batch_id}), follow=True)
        self.assertEqual(200, response.status_code)
        response = json.loads(response.content)
        candidate = models.ContentAdCandidate.objects.latest("created_dt")

        self.assertEqual(
            {
                "data": {
                    "candidate": {
                        "id": candidate.id,
                        "label": "",
                        "url": "",
                        "title": "",
                        "type": constants.AdType.CONTENT,
                        "image_url": None,
                        "image_crop": constants.ImageCrop.CENTER,
                        "display_url": "",
                        "brand_name": "",
                        "description": "",
                        "call_to_action": constants.DEFAULT_CALL_TO_ACTION,
                        "primary_tracker_url": None,
                        "secondary_tracker_url": None,
                        "image_hash": None,
                        "image_height": None,
                        "image_width": None,
                        "image_id": None,
                        "image_file_size": None,
                        "image_status": constants.AsyncUploadJobStatus.PENDING_START,
                        "url_status": constants.AsyncUploadJobStatus.PENDING_START,
                        "hosted_image_url": None,
                        "video_asset_id": None,
                        "ad_tag": None,
                        "additional_data": None,
                    }
                },
                "success": True,
            },
            response,
        )

    def test_add_candidate_with_id(self):
        batch_id = 1
        candidate_id = 1

        response = _get_client().post(
            reverse("upload_candidate", kwargs={"batch_id": batch_id, "candidate_id": candidate_id}), follow=True
        )
        self.assertEqual(400, response.status_code)

    def test_delete_candidate(self):
        batch_id = 5
        candidate_id = 4

        response = _get_client().delete(
            reverse("upload_candidate", kwargs={"batch_id": batch_id, "candidate_id": candidate_id}), follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual({"success": True}, json.loads(response.content))

        with self.assertRaises(models.ContentAdCandidate.DoesNotExist):
            models.ContentAdCandidate.objects.get(id=candidate_id)

    def test_delete_non_existing_candidate(self):
        batch_id = 5
        candidate_id = 555

        response = _get_client().delete(
            reverse("upload_candidate", kwargs={"batch_id": batch_id, "candidate_id": candidate_id}), follow=True
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            {"success": False, "data": {"error_code": "MissingDataError", "message": "Candidate does not exist"}},
            json.loads(response.content),
        )

    def test_delete_wrong_batch_id(self):
        ad_group = magic_mixer.blend(models.AdGroup)
        account = ad_group.campaign.account
        batch = magic_mixer.blend(models.UploadBatch, ad_group=ad_group, account=account)
        candidate_id = 4

        response = _get_client().delete(
            reverse("upload_candidate", kwargs={"batch_id": batch.id, "candidate_id": candidate_id}), follow=True
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            {"success": False, "data": {"error_code": "MissingDataError", "message": "Upload batch does not exist"}},
            json.loads(response.content),
        )


class CandidateUpdateTest(TestCase):

    fixtures = ["test_upload.yaml"]

    def test_update_candidate(self):
        batch_id = 5
        candidate_id = 4

        resource = {
            "candidate": {
                "id": 4,
                "label": "new label",
                "url": "http://zemanta.com/blog",
                "title": "New title",
                "image_url": "http://zemanta.com/img.jpg",
                "image_crop": "center",
                "display_url": "newurl.com",
                "brand_name": "New brand name",
                "description": "New description",
                "call_to_action": "New cta",
                "primary_tracker_url": "",
                "secondary_tracker_url": "",
            },
            "defaults": [],
        }

        response = _get_client().post(
            reverse("upload_candidate_update", kwargs={"batch_id": batch_id, "candidate_id": candidate_id}),
            {"data": json.dumps(resource)},
            follow=True,
        )
        self.assertEqual(200, response.status_code)

        response = json.loads(response.content)
        expected = {
            "data": {
                "updated_fields": {
                    "brand_name": "New brand name",
                    "call_to_action": "New cta",
                    "description": "New description",
                    "display_url": "newurl.com",
                    "image_crop": "center",
                    "image_url": "http://zemanta.com/img.jpg",
                    "label": "new label",
                    "primary_tracker_url": "",
                    "secondary_tracker_url": "",
                    "title": "New title",
                    "url": "http://zemanta.com/blog",
                },
                "errors": {},
            },
            "success": True,
        }
        self.assertEqual(expected, response)

    def test_non_existing_candidate(self):
        batch_id = 5
        candidate_id = 555

        resource = {
            "candidate": {
                "id": 555,
                "label": "new label",
                "url": "http://zemanta.com/blog",
                "title": "New title",
                "image_url": "http://zemanta.com/img.jpg",
                "image_crop": "center",
                "display_url": "newurl.com",
                "brand_name": "New brand name",
                "description": "New description",
                "call_to_action": "New cta",
                "primary_tracker_url": "",
                "secondary_tracker_url": "",
            },
            "defaults": [],
        }

        response = _get_client().post(
            reverse("upload_candidate_update", kwargs={"batch_id": batch_id, "candidate_id": candidate_id}),
            {"data": json.dumps(resource)},
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            {"success": False, "data": {"error_code": "MissingDataError", "message": "Candidate does not exist"}},
            json.loads(response.content),
        )

    def test_wrong_batch_id(self):
        ad_group = magic_mixer.blend(models.AdGroup)
        account = ad_group.campaign.account
        batch = magic_mixer.blend(models.UploadBatch, ad_group=ad_group, account=account)
        candidate_id = 4

        response = _get_client().post(
            reverse("upload_candidate_update", kwargs={"batch_id": batch.id, "candidate_id": candidate_id}),
            {"data": "x"},
            follow=True,
        )
        self.assertEqual(404, response.status_code)
        self.assertEqual(
            {"success": False, "data": {"error_code": "MissingDataError", "message": "Upload batch does not exist"}},
            json.loads(response.content),
        )
