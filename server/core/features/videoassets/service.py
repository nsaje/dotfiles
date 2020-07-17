import datetime
from collections import namedtuple

import requests
from defusedxml import ElementTree

from . import constants
from . import models

UploadInfo = namedtuple("UploadInfo", ["type", "url"])


class ParseVastError(Exception):
    pass


def initiate_asset_for_direct_upload(account, name):
    video_asset = models.VideoAsset.objects.create(constants.VideoAssetType.DIRECT_UPLOAD, account=account, name=name)
    return video_asset, UploadInfo(type=constants.VideoAssetType.DIRECT_UPLOAD, url=video_asset.get_s3_presigned_url())


def initiate_asset_for_vast_upload(account):
    video_asset = models.VideoAsset.objects.create(constants.VideoAssetType.VAST_UPLOAD, account=account)
    return video_asset, UploadInfo(type=constants.VideoAssetType.VAST_UPLOAD, url=video_asset.get_s3_presigned_url())


def create_asset_from_vast_url(account, vast_url):
    duration, formats = _parse_vast_from_url(vast_url)
    video_asset = models.VideoAsset.objects.create(
        constants.VideoAssetType.VAST_URL,
        account=account,
        status=constants.VideoAssetStatus.READY_FOR_USE,
        vast_url=vast_url,
        duration=duration,
        formats=formats,
    )
    return video_asset


def update_asset_for_vast_upload(account, video_asset_id):
    video_asset = models.VideoAsset.objects.get(account=account, id=video_asset_id)

    if not (
        video_asset.type == constants.VideoAssetType.VAST_UPLOAD
        and video_asset.status == constants.VideoAssetStatus.NOT_UPLOADED
    ):
        return

    duration, formats = _parse_vast_from_url(video_asset.get_vast_url(ready_for_use=False))

    video_asset.status = constants.VideoAssetStatus.READY_FOR_USE
    video_asset.duration = duration
    video_asset.formats = formats
    video_asset.save()

    return video_asset


def _parse_vast_from_url(vast_url):
    try:
        r = requests.get(vast_url)
    except requests.exceptions.RequestException:
        raise ParseVastError("Invalid url")
    if r.status_code != 200:
        raise ParseVastError("Invalid server response")

    try:
        return _parse_vast(r.content)
    except ParseVastError as e:
        raise ParseVastError("Invalid vast file: " + str(e))
    except ElementTree.ParseError:
        raise ParseVastError("Invalid xml file")


def _parse_vast(data):
    root = ElementTree.fromstring(data)
    if root.tag != "VAST":
        raise ParseVastError("Root tag must be VAST")

    ads = root.findall("Ad")
    if len(ads) != 1:
        raise ParseVastError("Multiple ads are not supported")
    ad = ads[0]

    inline = ad.find("InLine")
    wrapper = ad.find("Wrapper")
    if (inline is None and wrapper is None) or (inline is not None and wrapper is not None):
        raise ParseVastError("Must contain either InLine or Wrapper")

    if wrapper is not None:
        uri = wrapper.find("VASTAdTagURI")
        if uri is None:
            raise ParseVastError("Missing VASTAdTagURI in Wrapper")
        try:
            return _parse_vast_from_url(uri.text)
        except ParseVastError as e:
            raise ParseVastError("In wrapper: " + str(e))

    linears = list(inline.findall("Creatives/Creative/Linear"))
    if len(linears) != 1:
        raise ParseVastError("Ad must contain one Linear")
    linear = linears[0]

    duration = _parse_duration(linear.find("Duration"))
    formats = [_parse_media_file(media_file) for media_file in linear.findall("MediaFiles/MediaFile")]
    if len(formats) < 0:
        raise ParseVastError("Missing MediaFile")

    return duration, formats


def _parse_duration(duration_element):
    if duration_element is None:
        raise ParseVastError("Missing duration")

    duration = duration_element.text
    try:
        parts = duration.split(":")
        delta = datetime.timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))
        return int(delta.total_seconds())
    except Exception:
        raise ParseVastError("Invalid duration: {}".format(duration))


def _parse_media_file(media_file):
    def _get(name, typ=int, required=True):
        value = media_file.get(name)
        if value is None:
            if not required:
                return value
            raise ParseVastError("Missing MediaFile {}".format(name))
        try:
            return typ(value)
        except Exception:
            raise ParseVastError("Invalid MediaFile {}".format(name))

    return {
        "width": _get("width"),
        "height": _get("height"),
        "bitrate": _get("bitrate", required=False),
        "mime": _get("type", str),
        "filename": "",
    }
