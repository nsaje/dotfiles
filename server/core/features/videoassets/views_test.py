import mock
from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APIClient

from utils.magic_mixer import magic_mixer

import core.models.account
import restapi.common.views_base_test
from . import constants
from . import models


class VideoAssetTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        self.user = magic_mixer.blend_user(permissions=["fea_video_upload"])
        self.account = magic_mixer.blend(core.models.Account, users=[self.user])
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        patcher = mock.patch("boto3.client")
        self.boto3_get_client = patcher.start()
        self.addCleanup(patcher.stop)

    def test_permissions(self):
        video_asset = magic_mixer.blend(models.VideoAsset)
        r = self.client.get(
            reverse("videoassets_details", kwargs=dict(videoasset_id=video_asset.id, account_id=video_asset.account.id))
        )
        r = self.assertResponseError(r, "MissingDataError")

    def test_get(self):
        video_asset = magic_mixer.blend(models.VideoAsset, account=self.account, name="myvideo", error_code="4006")
        r = self.client.get(
            reverse("videoassets_details", kwargs=dict(videoasset_id=video_asset.id, account_id=video_asset.account.id))
        )
        r = self.assertResponseValid(r)
        self.assertEqual(r["data"]["name"], video_asset.name)
        self.assertEqual(r["data"]["errorCode"], video_asset.error_code)

    @override_settings(VAST_URL="http://vasttest.com/{filename}")
    @mock.patch("core.features.videoassets.service.parse_vast_from_url")
    def test_put(self, mock_parse):
        mock_parse.return_value = 30, []
        video_asset = magic_mixer.blend(
            models.VideoAsset,
            account=self.account,
            name="",
            type=constants.VideoAssetType.VAST_UPLOAD,
            status=constants.VideoAssetStatus.NOT_UPLOADED,
        )
        r = self.client.put(
            reverse(
                "videoassets_details", kwargs=dict(videoasset_id=video_asset.id, account_id=video_asset.account.id)
            ),
            data={"status": "PROCESSING"},
            format="json",
        )

        url = "http://vasttest.com/" + str(video_asset.id)

        r = self.assertResponseValid(r)
        self.assertEqual(r["data"]["name"], "")
        self.assertEqual(r["data"]["type"], "VAST_UPLOAD")
        self.assertEqual(r["data"]["vastUrl"], url)
        self.assertEqual(r["data"]["account"], str(self.account.id))
        self.assertEqual(r["data"]["status"], "READY_FOR_USE")

        mock_parse.assert_called_once_with(url)

    def test_post_direct_upload(self):
        mock_s3_client = mock.Mock()
        mock_s3_client.generate_presigned_url.return_value = "http://mypresigned.com"
        self.boto3_get_client.return_value = mock_s3_client
        data = {"name": "myvideo", "upload": {"type": "DIRECT_UPLOAD"}}
        r = self.client.post(
            reverse("videoassets_list", kwargs=dict(account_id=self.account.id)), data=data, format="json"
        )
        r = self.assertResponseValid(r)
        self.assertEqual(r["data"]["name"], "myvideo")
        self.assertEqual(r["data"]["type"], "DIRECT_UPLOAD")
        self.assertEqual(r["data"]["account"], str(self.account.id))
        self.assertEqual(r["data"]["status"], "NOT_UPLOADED")
        self.assertEqual(r["data"]["upload"]["url"], "http://mypresigned.com")

        mock_s3_client.generate_presigned_url.assert_called_once()

    def test_post_vast_upload(self):
        mock_s3_client = mock.Mock()
        mock_s3_client.generate_presigned_url.return_value = "http://mypresigned.com"
        self.boto3_get_client.return_value = mock_s3_client
        data = {"name": "myvideo", "upload": {"type": "VAST_UPLOAD"}}
        r = self.client.post(
            reverse("videoassets_list", kwargs=dict(account_id=self.account.id)), data=data, format="json"
        )
        r = self.assertResponseValid(r)
        self.assertEqual(r["data"]["name"], "")
        self.assertEqual(r["data"]["type"], "VAST_UPLOAD")
        self.assertEqual(r["data"]["account"], str(self.account.id))
        self.assertEqual(r["data"]["status"], "NOT_UPLOADED")
        self.assertEqual(r["data"]["upload"]["url"], "http://mypresigned.com")

        mock_s3_client.generate_presigned_url.assert_called_once()

    @mock.patch("core.features.videoassets.service.parse_vast_from_url")
    def test_post_vast_url(self, mock_parse):
        mock_parse.return_value = 30, []
        data = {"name": "myvideo", "vast_url": "http://vasturl.com", "upload": {"type": "VAST_URL"}}
        r = self.client.post(
            reverse("videoassets_list", kwargs=dict(account_id=self.account.id)), data=data, format="json"
        )
        r = self.assertResponseValid(r)
        self.assertEqual(r["data"]["name"], "")
        self.assertEqual(r["data"]["type"], "VAST_URL")
        self.assertEqual(r["data"]["vastUrl"], "http://vasturl.com")
        self.assertEqual(r["data"]["account"], str(self.account.id))
        self.assertEqual(r["data"]["status"], "READY_FOR_USE")

        mock_parse.assert_called_once_with("http://vasturl.com")
