from collections import namedtuple

from . import constants
from . import models


UploadInfo = namedtuple('UploadInfo', ['type', 'url'])


def initiate_asset_for_direct_upload(account, name):
    video_asset = models.VideoAsset.objects.create(constants.VideoAssetType.DIRECT_UPLOAD, account=account, name=name)
    return video_asset, UploadInfo(
        type=constants.VideoAssetType.DIRECT_UPLOAD,
        url=video_asset.get_s3_presigned_url()
    )


def initiate_asset_for_vast_upload(account):
    video_asset = models.VideoAsset.objects.create(constants.VideoAssetType.VAST_UPLOAD, account=account)
    return video_asset, UploadInfo(
        type=constants.VideoAssetType.VAST_UPLOAD,
        url=video_asset.get_s3_presigned_url()
    )


def create_asset_from_vast_url(account, vast_url):
    video_asset = models.VideoAsset.objects.create(
        constants.VideoAssetType.VAST_URL, account=account, status=constants.VideoAssetStatus.READY_FOR_USE, vast_url=vast_url)
    return video_asset
