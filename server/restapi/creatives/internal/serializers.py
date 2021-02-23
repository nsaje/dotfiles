import rest_framework.serializers

import core.features.videoassets.models
import dash.constants
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
import restapi.serializers.trackers
from core.models.tags import CreativeTag

from . import validators


class AdTypeSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(dash.constants.AdType, required=True)


class CreativeCommonSerializer(AdTypeSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)

    agency_id = restapi.serializers.fields.IdField(read_only=True)
    account_id = restapi.serializers.fields.IdField(read_only=True)

    url = rest_framework.serializers.URLField(required=True)
    title = restapi.serializers.fields.PlainCharField(required=True)
    display_url = rest_framework.serializers.URLField(required=True)

    tags = rest_framework.serializers.ListSerializer(child=rest_framework.serializers.CharField(), default=[])
    trackers = restapi.serializers.trackers.TrackersSerializer(allow_null=True, required=False)


class NativeCreativeSerializer(CreativeCommonSerializer):
    brand_name = restapi.serializers.fields.PlainCharField(required=True)
    description = restapi.serializers.fields.PlainCharField(required=True)
    call_to_action = restapi.serializers.fields.PlainCharField(required=True)
    image_crop = restapi.serializers.fields.PlainCharField(required=True)

    image_id = restapi.serializers.fields.PlainCharField(max_length=256, required=True)
    image_hash = restapi.serializers.fields.PlainCharField(max_length=128, required=True)
    image_width = rest_framework.serializers.IntegerField(required=True)
    image_height = rest_framework.serializers.IntegerField(required=True)
    image_file_size = rest_framework.serializers.IntegerField(required=True)
    image_url = rest_framework.serializers.URLField(required=True)

    icon_id = restapi.serializers.fields.PlainCharField(max_length=256, required=True)
    icon_hash = restapi.serializers.fields.PlainCharField(max_length=128, required=True)
    icon_width = rest_framework.serializers.IntegerField(required=True)
    icon_height = rest_framework.serializers.IntegerField(required=True)
    icon_file_size = rest_framework.serializers.IntegerField(required=True)
    icon_url = rest_framework.serializers.URLField(required=True)


class VideoCreativeSerializer(NativeCreativeSerializer):
    video_asset_id = rest_framework.serializers.UUIDField(required=True)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        # TODO (msuber): add video asset scope validation
        video_asset_id = value.get("video_asset_id")
        value["video_asset"] = (
            core.features.videoassets.models.VideoAsset.objects.get(pk=video_asset_id)
            if video_asset_id is not None
            else None
        )

        return value


class ImageCreativeSerializer(CreativeCommonSerializer):
    image_id = restapi.serializers.fields.PlainCharField(max_length=256, required=True)
    image_hash = restapi.serializers.fields.PlainCharField(max_length=128, required=True)
    image_width = rest_framework.serializers.IntegerField(required=True)
    image_height = rest_framework.serializers.IntegerField(required=True)
    image_file_size = rest_framework.serializers.IntegerField(required=True)
    image_url = rest_framework.serializers.URLField(required=True)


class AdTagCreativeSerializer(CreativeCommonSerializer):
    image_width = rest_framework.serializers.IntegerField(required=True)
    image_height = rest_framework.serializers.IntegerField(required=True)
    ad_tag = rest_framework.serializers.CharField(required=True)

    def validate_image_width(self, value):
        validators.validate_ad_width(value)
        return value

    def validate_image_height(self, value):
        validators.validate_ad_height(value)
        return value

    def validate(self, value):
        validators.validate_ad_size_variants(value.get("image_width"), value.get("image_height"))
        return value


class CreativeSerializer(VideoCreativeSerializer, ImageCreativeSerializer, AdTagCreativeSerializer):
    def __init__(self, *args, **kwargs):
        super(CreativeSerializer, self).__init__(*args, **kwargs)
        self.fields.pop("image_id")
        self.fields.pop("image_hash")
        self.fields.pop("image_width")
        self.fields.pop("image_height")
        self.fields.pop("image_file_size")

        self.fields.pop("icon_id")
        self.fields.pop("icon_hash")
        self.fields.pop("icon_width")
        self.fields.pop("icon_height")
        self.fields.pop("icon_file_size")

    image_url = rest_framework.serializers.URLField(source="get_image_url", read_only=True)
    icon_url = rest_framework.serializers.URLField(source="get_icon_url", read_only=True)

    hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    landscape_hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    portrait_hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    display_hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    hosted_icon_url = rest_framework.serializers.URLField(read_only=True)


class CreativeQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    keyword = restapi.serializers.fields.PlainCharField(required=False)
    creative_type = restapi.serializers.fields.DashConstantField(dash.constants.AdType, required=False)
    tags = restapi.serializers.fields.PlainCharField(required=False)

    def validate_tags(self, value):
        tags = value.split(",")
        count = CreativeTag.objects.filter(name__in=tags).count()
        if len(tags) > count:
            raise rest_framework.serializers.ValidationError(["Invalid tags"])
        return tags


class CreativeBatchSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)

    agency_id = restapi.serializers.fields.IdField(allow_null=True, required=False)
    account_id = restapi.serializers.fields.IdField(allow_null=True, required=False)

    name = rest_framework.serializers.CharField(max_length=1024, allow_null=True, allow_blank=True, required=False)
    mode = restapi.serializers.fields.DashConstantField(
        dash.constants.CreativeBatchMode, default=dash.constants.CreativeBatchMode.INSERT
    )
    type = restapi.serializers.fields.DashConstantField(
        dash.constants.CreativeBatchType, default=dash.constants.CreativeBatchType.NATIVE
    )

    tags = rest_framework.serializers.ListSerializer(child=rest_framework.serializers.CharField(), default=[])
    image_crop = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)
    display_url = rest_framework.serializers.URLField(allow_blank=True, allow_null=True, required=False)
    brand_name = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)
    description = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)
    call_to_action = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)

    created_by = rest_framework.serializers.EmailField(read_only=True)
    created_dt = rest_framework.serializers.DateTimeField(read_only=True)


class CreativeCandidateCommonSerializer(AdTypeSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    original_creative_id = restapi.serializers.fields.IdField(read_only=True)

    url = rest_framework.serializers.URLField(required=True)
    title = restapi.serializers.fields.PlainCharField(required=True)
    display_url = rest_framework.serializers.URLField(required=True)

    tags = rest_framework.serializers.ListSerializer(child=rest_framework.serializers.CharField(), default=[])
    trackers = restapi.serializers.trackers.TrackersSerializer(allow_null=True, required=False)


class NativeCreativeCandidateSerializer(CreativeCandidateCommonSerializer):
    brand_name = restapi.serializers.fields.PlainCharField(required=True)
    description = restapi.serializers.fields.PlainCharField(required=True)
    call_to_action = restapi.serializers.fields.PlainCharField(required=True)
    image_crop = restapi.serializers.fields.PlainCharField(required=True)

    image_url = rest_framework.serializers.URLField(required=False)
    image = rest_framework.serializers.ImageField(max_length=1024, allow_empty_file=False, required=False)

    icon_url = rest_framework.serializers.URLField(required=False)
    icon = rest_framework.serializers.ImageField(max_length=1024, allow_empty_file=False, required=False)


class VideoCreativeCandidateSerializer(NativeCreativeCandidateSerializer):
    video_asset_id = rest_framework.serializers.UUIDField(required=True)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        # TODO (msuber): add video asset scope validation
        video_asset_id = value.get("video_asset_id")
        value["video_asset"] = (
            core.features.videoassets.models.VideoAsset.objects.get(pk=video_asset_id)
            if video_asset_id is not None
            else None
        )

        return value


class ImageCreativeCandidateSerializer(CreativeCandidateCommonSerializer):
    image_url = rest_framework.serializers.URLField(required=False)
    image = rest_framework.serializers.ImageField(max_length=1024, allow_empty_file=False, required=False)


class AdTagCreativeCandidateSerializer(CreativeCandidateCommonSerializer):
    image_width = rest_framework.serializers.IntegerField(required=True)
    image_height = rest_framework.serializers.IntegerField(required=True)
    ad_tag = rest_framework.serializers.CharField(required=True)

    def validate_image_width(self, value):
        validators.validate_ad_width(value)
        return value

    def validate_image_height(self, value):
        validators.validate_ad_height(value)
        return value

    def validate(self, value):
        validators.validate_ad_size_variants(value.get("image_width"), value.get("image_height"))
        return value


# TODO (msuber): add trackers_status
class CreativeCandidateSerializer(
    VideoCreativeCandidateSerializer, ImageCreativeCandidateSerializer, AdTagCreativeCandidateSerializer
):
    url_status = restapi.serializers.fields.DashConstantField(
        dash.constants.AsyncUploadJobStatus, default=dash.constants.AsyncUploadJobStatus.PENDING_START, read_only=True
    )
    image_status = restapi.serializers.fields.DashConstantField(
        dash.constants.AsyncUploadJobStatus, default=dash.constants.AsyncUploadJobStatus.PENDING_START, read_only=True
    )
    icon_status = restapi.serializers.fields.DashConstantField(
        dash.constants.AsyncUploadJobStatus, default=dash.constants.AsyncUploadJobStatus.PENDING_START, read_only=True
    )

    hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    landscape_hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    portrait_hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    display_hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    hosted_icon_url = rest_framework.serializers.URLField(read_only=True)
