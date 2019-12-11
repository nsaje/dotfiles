import django.db.utils
import mock
from django.conf import settings
from django.test import TestCase
from django.test import override_settings

import core.models

from . import exceptions


@override_settings(LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME="test_mock")
class ImageAssetManagerTest(TestCase):
    @mock.patch("utils.lambda_helper.invoke_lambda")
    def test_external_validation_fail(self, mock_external_validation):
        mock_external_validation.return_value = {
            "status": "fail",
            "error": {"message": "error_message"},
            "candidate": {
                "images": {
                    "http://image.url.com": {
                        "valid": True,
                        "id": "image_id",
                        "hash": "image_hash",
                        "width": 190,
                        "height": 200,
                        "file_size": 9000,
                    }
                }
            },
        }
        with self.assertRaises(exceptions.ImageAssetExternalValidationFailed):
            core.models.ImageAsset.objects._invoke_external_validation("http://image.url.com")

        mock_external_validation.return_value["status"] = "ok"
        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["valid"] = False
        with self.assertRaises(exceptions.ImageAssetInvalid):
            core.models.ImageAsset.objects._invoke_external_validation("http://image.url.com")

        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["valid"] = True
        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["id"] = None
        with self.assertRaises(exceptions.ImageAssetInvalid):
            core.models.ImageAsset.objects._invoke_external_validation("http://image.url.com")

        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["id"] = "image_id"
        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["hash"] = None
        with self.assertRaises(exceptions.ImageAssetInvalid):
            core.models.ImageAsset.objects._invoke_external_validation("http://image.url.com")

        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["hash"] = "image_hash"
        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["width"] = None
        with self.assertRaises(exceptions.ImageAssetInvalid):
            core.models.ImageAsset.objects._invoke_external_validation("http://image.url.com")

        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["width"] = 190
        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["height"] = None
        with self.assertRaises(exceptions.ImageAssetInvalid):
            core.models.ImageAsset.objects._invoke_external_validation("http://image.url.com")

        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["height"] = 200
        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["file_size"] = None
        with self.assertRaises(exceptions.ImageAssetInvalid):
            core.models.ImageAsset.objects._invoke_external_validation("http://image.url.com")

        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["file_size"] = 9000
        image_data = core.models.ImageAsset.objects._invoke_external_validation("http://image.url.com")

        self.assertTrue(image_data["valid"])
        self.assertEqual("image_id", image_data["id"])
        self.assertEqual("image_hash", image_data["hash"])
        self.assertEqual(190, image_data["width"])
        self.assertEqual(200, image_data["height"])
        self.assertEqual(9000, image_data["file_size"])

    @mock.patch("dash.image_helper.upload_image_to_s3", return_value="image.url")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    def test_create_from_origin_url(self, mock_external_validation, mock_s3_upload):
        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "http://image.url.com": {
                        "valid": True,
                        "id": "image_id",
                        "hash": "image_hash",
                        "width": 190,
                        "height": 200,
                        "file_size": 9000,
                    }
                }
            },
        }
        image_asset = core.models.ImageAsset.objects.create_from_origin_url("http://image.url.com")
        self.assertEqual("image_id", image_asset.image_id)
        self.assertEqual("image_hash", image_asset.image_hash)
        self.assertEqual(190, image_asset.width)
        self.assertEqual(200, image_asset.height)
        self.assertEqual(9000, image_asset.file_size)
        self.assertEqual("http://image.url.com", image_asset.origin_url)

        mock_s3_upload.assert_not_called()

    @mock.patch("dash.image_helper.upload_image_to_s3", return_value="image.url")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    def test_create_from_image_base64(self, mock_external_validation, mock_s3_upload):
        mock_external_validation.return_value = {
            "status": "ok",
            "candidate": {
                "images": {
                    "image.url": {
                        "valid": True,
                        "id": "image_id",
                        "hash": "image_hash",
                        "width": 190,
                        "height": 200,
                        "file_size": 9000,
                    }
                }
            },
        }
        image_asset = core.models.ImageAsset.objects.create_from_image_base64("image_base64", "upload_id")
        self.assertEqual("image_id", image_asset.image_id)
        self.assertEqual("image_hash", image_asset.image_hash)
        self.assertEqual(190, image_asset.width)
        self.assertEqual(200, image_asset.height)
        self.assertEqual(9000, image_asset.file_size)
        self.assertIsNone(image_asset.origin_url)

        mock_s3_upload.assert_called_once_with("image_base64", "upload_id")

    @mock.patch("dash.image_helper.upload_image_to_s3", return_value="image.url")
    @mock.patch("utils.lambda_helper.invoke_lambda")
    def test_exists_update_origin_url(self, mock_external_validation, mock_s3_upload):
        s3_origin_url = settings.IMAGE_THUMBNAIL_URL + "test"
        image_data = {"valid": True, "id": "image_id", "hash": "hash", "width": 250, "height": 250, "file_size": 2500}
        mock_external_validation.return_value = {"status": "ok", "candidate": {"images": {s3_origin_url: image_data}}}
        image_asset = core.models.ImageAsset.objects.create(
            image_id="image_id", image_hash="hash", width=250, height=250, file_size=2500
        )
        image_asset.save()
        self.assertIsNone(image_asset.origin_url)
        self.assertEqual(1, core.models.ImageAsset.objects.all().count())

        new_image_asset = core.models.ImageAsset.objects.create_from_origin_url(s3_origin_url)
        self.assertEqual(1, core.models.ImageAsset.objects.all().count())

        image_asset.refresh_from_db()
        self.assertEqual("image_id", new_image_asset.image_id)
        self.assertEqual(image_asset.image_id, new_image_asset.image_id)
        self.assertEqual(s3_origin_url, image_asset.origin_url)

        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"] = image_data
        new_image_asset = core.models.ImageAsset.objects.create_from_origin_url("http://image.url.com")
        self.assertEqual(1, core.models.ImageAsset.objects.all().count())

        image_asset.refresh_from_db()
        self.assertEqual("image_id", new_image_asset.image_id)
        self.assertEqual(image_asset.image_id, new_image_asset.image_id)
        self.assertEqual("http://image.url.com", image_asset.origin_url)

    def test_create(self):
        image_asset = core.models.ImageAsset.objects.create(
            image_id="image_id", image_hash="hash", width=250, height=250, file_size=2500
        )
        image_asset.save()
        self.assertIsNone(image_asset.origin_url)
        self.assertEqual(1, core.models.ImageAsset.objects.all().count())

        new_image_asset = core.models.ImageAsset.objects.create(
            image_id="image_id",
            image_hash="hash",
            width=250,
            height=250,
            file_size=2500,
            origin_url="http://image.url.com",
        )
        self.assertEqual(1, core.models.ImageAsset.objects.all().count())

        image_asset.refresh_from_db()
        self.assertEqual("image_id", new_image_asset.image_id)
        self.assertEqual(image_asset.image_id, new_image_asset.image_id)
        self.assertEqual("http://image.url.com", image_asset.origin_url)

        with self.assertRaises(django.db.utils.IntegrityError):
            core.models.ImageAsset.objects.create(
                image_id="image_id", image_hash="hash", width=250, height=250, file_size=2501
            )
