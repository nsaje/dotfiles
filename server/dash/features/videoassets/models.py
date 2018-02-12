import uuid
import boto3
import jsonfield

from django.db import models
from django.conf import settings

from . import constants


S3_UPLOAD_PATH_FORMAT = 'upload/{videoasset_id}'


ERROR_CODE_MESSAGES = {
    '4000': "File format not supported",
    '4001': "Width and height too large",
    '4002': "File size too large",
    '4006': "File format not supported",
    '4008': "Invalid file: Missing audio or video",
    '4100': "Invalid file: Could not interpret embedded caption track",
}


def validate_format(item):
    assert isinstance(item.get('width'), int)
    assert isinstance(item.get('height'), int)
    assert isinstance(item.get('bitrate'), int)
    assert isinstance(item.get('mime'), str)
    assert isinstance(item.get('filename'), str)


class VideoAssetManager(models.Manager):

    def create(self, account, name):
        video_asset = VideoAsset(account=account, name=name)
        video_asset.save()
        return video_asset


class VideoAsset(models.Model):
    objects = VideoAssetManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey('Account', on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')
    status = models.IntegerField(
        default=constants.VideoAssetStatus.NOT_UPLOADED,
        choices=constants.VideoAssetStatus.get_choices()
    )
    error_code = models.CharField(max_length=20, blank=True, null=True)

    name = models.CharField(max_length=255)
    duration = models.IntegerField(null=True, blank=True)
    formats = jsonfield.fields.JSONField(blank=True, null=True)

    def get_s3_presigned_url(self):
        if self.status != constants.VideoAssetStatus.NOT_UPLOADED:
            raise ValueError("Cannot get an upload url for an already uploaded video")
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': settings.S3_BUCKET_VIDEO,
                'Key': S3_UPLOAD_PATH_FORMAT.format(videoasset_id=self.id),
                'ContentType': 'application/octet-stream',
                'Metadata': {
                    'videoassetid': str(self.id),
                    'callbackhost': settings.LAMBDA_CALLBACK_HOST,
                    'environment': settings.LAMBDA_ENVIRONMENT,
                },
            }
        )
        return url

    def get_status_message(self):
        return constants.VideoAssetStatus.get_text(self.status)

    def get_error_message(self):
        if self.error_code:
            return ERROR_CODE_MESSAGES.get(self.error_code, "Unknown error, please contact support.")

    def get_preview_url(self):
        if self.status == constants.VideoAssetStatus.READY_FOR_USE and self.formats and len(self.formats) > 0:
            format = self.formats[0]
            return settings.VIDEO_PREVIEW_URL.format(filename=format['filename'])

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
