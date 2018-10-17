import uuid
import boto3
import jsonfield

from django.db import models
from django.conf import settings

from utils.json_helper import JSONFIELD_DUMP_KWARGS
from . import constants


S3_DIRECT_UPLOAD_PATH_FORMAT = "upload/{videoasset_id}"
S3_VAST_UPLOAD_PATH_FORMAT = "vast/{videoasset_id}"


ERROR_CODE_MESSAGES = {
    "4000": "File format not supported",
    "4001": "Width and height too large",
    "4002": "File size too large",
    "4006": "File format not supported",
    "4008": "Invalid file: Missing audio or video",
    "4100": "Invalid file: Could not interpret embedded caption track",
    "5000": "Invalid vast file",
}


def validate_format(item):
    assert isinstance(item.get("width"), int)
    assert isinstance(item.get("height"), int)
    assert isinstance(item.get("bitrate"), int)
    assert isinstance(item.get("mime"), str)
    assert isinstance(item.get("filename"), str)


class VideoAssetManager(models.Manager):
    def create(self, type, account, **kwargs):
        video_asset = VideoAsset(type=type, account=account, **kwargs)
        video_asset.save()
        return video_asset


class VideoAsset(models.Model):
    class Meta:
        app_label = "dash"

    objects = VideoAssetManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey("Account", on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    status = models.IntegerField(
        default=constants.VideoAssetStatus.NOT_UPLOADED, choices=constants.VideoAssetStatus.get_choices()
    )
    error_code = models.CharField(max_length=20, blank=True, null=True)

    name = models.CharField(max_length=255)
    duration = models.IntegerField(null=True, blank=True)
    formats = jsonfield.fields.JSONField(blank=True, null=True, dump_kwargs=JSONFIELD_DUMP_KWARGS)

    type = models.IntegerField(
        default=constants.VideoAssetType.DIRECT_UPLOAD, choices=constants.VideoAssetType.get_choices()
    )
    vast_url = models.CharField(max_length=2048, blank=True, null=True)

    def get_s3_presigned_url(self):
        if self.status != constants.VideoAssetStatus.NOT_UPLOADED:
            raise ValueError("Cannot get an upload url for an already uploaded video")

        if self.type == constants.VideoAssetType.DIRECT_UPLOAD:
            key = S3_DIRECT_UPLOAD_PATH_FORMAT.format(videoasset_id=self.id)
            content_type = "application/octet-stream"
        elif self.type == constants.VideoAssetType.VAST_UPLOAD:
            key = S3_VAST_UPLOAD_PATH_FORMAT.format(videoasset_id=self.id)
            content_type = "text/xml"
        else:
            raise ValueError("Cannot get an upload url for this type of video asset")

        s3 = boto3.client("s3")
        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.S3_BUCKET_VIDEO,
                "Key": key,
                "ContentType": content_type,
                "Metadata": {
                    "videoassetid": str(self.id),
                    "callbackhost": settings.LAMBDA_CALLBACK_HOST,
                    "environment": settings.LAMBDA_ENVIRONMENT,
                },
            },
        )
        return url

    def get_vast_url(self, ready_for_use=True):
        if ready_for_use and self.status != constants.VideoAssetStatus.READY_FOR_USE:
            return None
        if self.type == constants.VideoAssetType.VAST_UPLOAD:
            return settings.VAST_URL.format(filename=self.id)
        return self.vast_url

    def get_status_message(self):
        return constants.VideoAssetStatus.get_text(self.status)

    def get_error_message(self):
        if self.error_code:
            return ERROR_CODE_MESSAGES.get(self.error_code, "Unknown error, please contact support.")

    def get_preview_url(self):
        if self.status == constants.VideoAssetStatus.READY_FOR_USE and self.formats and len(self.formats) > 0:
            format = self.formats[0]
            return settings.VIDEO_PREVIEW_URL.format(filename=format["filename"])

    def update_progress(self, status, error_code=None, duration=None, formats=None):
        self.status = status
        if error_code is not None:
            self.error_code = error_code
        if duration is not None:
            self.duration = duration
        if formats is not None:
            for item in formats:
                validate_format(item)
            self.formats = formats
        self.save()
