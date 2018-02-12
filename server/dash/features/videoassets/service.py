from collections import namedtuple

from . import models
from . import serializers


UploadInfo = namedtuple('UploadInfo', ['type', 'url'])


def initiate_asset_for_direct_upload(account, name):
    video_asset = models.VideoAsset.objects.create(account=account, name=name)
    return video_asset, UploadInfo(
        type=serializers.DIRECT_UPLOAD,
        url=video_asset.get_s3_presigned_url()
    )
