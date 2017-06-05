import uuid
import boto3

from django.db import models
from django.conf import settings

import constants


S3_UPLOAD_PATH_FORMAT = 'upload/{videoasset_id}'


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
    name = models.CharField(max_length=255)

    def get_s3_presigned_url(self):
        if self.status != constants.VideoAssetStatus.NOT_UPLOADED:
            raise ValueError("Cannot get an upload url for an already uploaded video")
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': settings.S3_BUCKET_VIDEO,
                'Key': S3_UPLOAD_PATH_FORMAT.format(videoasset_id=self.id),
                'ContentType': 'application/octet-stream'
            }
        )
        return url

    def get_status_message(self):
        return constants.VideoAssetStatus.get_text(self.status)

    def set_status(self, new_status):
        self.status = new_status
        self.save()
