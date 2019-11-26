from django.conf import settings
from django.db import models

import dash.constants
import dash.image_helper
import utils.lambda_helper

from . import exceptions
from . import model


class ImageAssetManager(models.Manager):
    def create_from_origin_url(self, origin_url, crop=None):
        image_data = self._invoke_external_validation(origin_url)
        image = model.ImageAsset(
            image_id=image_data["id"],
            hash=image_data["hash"],
            width=image_data["width"],
            height=image_data["height"],
            crop=crop or dash.constants.ImageCrop.CENTER,
            file_size=image_data["file_size"],
            origin_url=origin_url,
        )
        image.save()
        return image

    def create_from_image_base64(self, image_base64, upload_id, crop=None):
        image_url = dash.image_helper.upload_image_to_s3(image_base64, upload_id)
        image_data = self._invoke_external_validation(image_url)
        image = model.ImageAsset(
            image_id=image_data["id"],
            hash=image_data["hash"],
            width=image_data["width"],
            height=image_data["height"],
            crop=crop or dash.constants.ImageCrop.CENTER,
            file_size=image_data["file_size"],
        )
        image.save()
        return image

    def _invoke_external_validation(self, image_url):
        payload = {
            "namespace": settings.LAMBDA_CONTENT_UPLOAD_NAMESPACE,
            "candidateID": 0,
            "adGroupID": 0,
            "pageUrl": "",
            "skipUrlValidation": True,
            "imageUrls": [image_url],
            "normalize": True,
        }
        result = utils.lambda_helper.invoke_lambda(
            settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME, payload, do_async=False
        )
        if result["status"] != "ok":
            raise exceptions.ImageAssetExternalValidationFailed(result["error"]["message"])

        image_data = result["candidate"]["images"][image_url]

        if not image_data["valid"] or not all(
            image_data.get(field) for field in ["id", "hash", "width", "height", "file_size"]
        ):
            raise exceptions.ImageAssetInvalid("Image asset could not be processed.")

        return image_data
