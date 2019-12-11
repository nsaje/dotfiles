from django.conf import settings
from django.db import models

import dash.constants
import dash.image_helper
import utils.lambda_helper

from . import exceptions
from . import model


class ImageAssetManager(models.Manager):
    def create_from_origin_url(self, origin_url):
        image_url = origin_url.split("?")[0]
        image_data = self._invoke_external_validation(image_url)
        return self.create(
            image_id=image_data["id"],
            image_hash=image_data["hash"],
            width=image_data["width"],
            height=image_data["height"],
            file_size=image_data["file_size"],
            origin_url=image_url,
        )

    def create_from_image_base64(self, image_base64, upload_id):
        image_url = dash.image_helper.upload_image_to_s3(image_base64, upload_id)
        image_data = self._invoke_external_validation(image_url)
        return self.create(
            image_id=image_data["id"],
            image_hash=image_data["hash"],
            width=image_data["width"],
            height=image_data["height"],
            file_size=image_data["file_size"],
        )

    def create(self, image_id, image_hash, width, height, file_size, origin_url=None):
        try:
            image = model.ImageAsset.objects.get(
                image_id=image_id, image_hash=image_hash, width=width, height=height, file_size=file_size
            )

            #  Origin url can be the url from the temp bucket on s3 when uploading an image directly.
            #  It can either be updated with a newer s3 url or user's source one.
            if origin_url and (not image.origin_url or image.origin_url.startswith(settings.IMAGE_THUMBNAIL_URL)):
                image.origin_url = origin_url
                image.save()

            return image

        except model.ImageAsset.DoesNotExist:
            image = model.ImageAsset(
                image_id=image_id,
                image_hash=image_hash,
                width=width,
                height=height,
                file_size=file_size,
                origin_url=origin_url,
            )
            image.save()
            return image

    def _invoke_external_validation(self, image_url):
        if settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME == "mock":
            return self._external_validation_mock()

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

    def _external_validation_mock(self):
        assert settings.DEBUG or settings.TESTING
        data = {"id": "d/icons/IAB2", "hash": "mock_image_hash", "width": 280, "height": 280, "file_size": 2800}
        return data
