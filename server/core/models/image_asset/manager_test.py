import mock
from django.test import TestCase

import core.models
import dash.constants

from . import exceptions


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
        self.assertEqual("image_hash", image_asset.hash)
        self.assertEqual(190, image_asset.width)
        self.assertEqual(200, image_asset.height)
        self.assertEqual(dash.constants.ImageCrop.CENTER, image_asset.crop)
        self.assertEqual(9000, image_asset.file_size)
        self.assertEqual("http://image.url.com", image_asset.origin_url)

        mock_external_validation.return_value["candidate"]["images"]["http://image.url.com"]["id"] = "image_id_2"
        image_asset = core.models.ImageAsset.objects.create_from_origin_url(
            "http://image.url.com", crop=dash.constants.ImageCrop.ENTROPY
        )
        self.assertEqual("image_id_2", image_asset.image_id)
        self.assertEqual("image_hash", image_asset.hash)
        self.assertEqual(190, image_asset.width)
        self.assertEqual(200, image_asset.height)
        self.assertEqual(dash.constants.ImageCrop.ENTROPY, image_asset.crop)
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
        image_asset = core.models.ImageAsset.objects.create_from_image_base64("image_base64_1", "upload_id1")
        self.assertEqual("image_id", image_asset.image_id)
        self.assertEqual("image_hash", image_asset.hash)
        self.assertEqual(190, image_asset.width)
        self.assertEqual(200, image_asset.height)
        self.assertEqual(dash.constants.ImageCrop.CENTER, image_asset.crop)
        self.assertEqual(9000, image_asset.file_size)
        self.assertIsNone(image_asset.origin_url)

        mock_external_validation.return_value["candidate"]["images"]["image.url"]["id"] = "image_id_2"
        image_asset = core.models.ImageAsset.objects.create_from_image_base64(
            "image_base64_2", "upload_id2", crop=dash.constants.ImageCrop.FACES
        )
        self.assertEqual("image_id_2", image_asset.image_id)
        self.assertEqual("image_hash", image_asset.hash)
        self.assertEqual(190, image_asset.width)
        self.assertEqual(200, image_asset.height)
        self.assertEqual(dash.constants.ImageCrop.FACES, image_asset.crop)
        self.assertEqual(9000, image_asset.file_size)
        self.assertIsNone(image_asset.origin_url)

        self.assertEqual(2, mock_s3_upload.call_count)
        self.assertEqual(
            [mock.call("image_base64_1", "upload_id1"), mock.call("image_base64_2", "upload_id2")],
            mock_s3_upload.call_args_list,
        )
