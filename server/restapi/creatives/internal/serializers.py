import rest_framework.serializers

import dash.constants
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
import restapi.serializers.trackers
from core.models.tags import CreativeTag


class CreativeSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)

    agency_id = restapi.serializers.fields.IdField(read_only=True)
    account_id = restapi.serializers.fields.IdField(read_only=True)

    type = restapi.serializers.fields.DashConstantField(
        dash.constants.AdType, default=dash.constants.AdType.CONTENT, read_only=True
    )

    url = rest_framework.serializers.URLField(read_only=True)
    title = rest_framework.serializers.CharField(read_only=True)
    display_url = rest_framework.serializers.URLField(read_only=True)
    brand_name = rest_framework.serializers.CharField(read_only=True)
    description = rest_framework.serializers.CharField(read_only=True)
    call_to_action = rest_framework.serializers.CharField(read_only=True)

    tags = rest_framework.serializers.ListSerializer(
        child=rest_framework.serializers.CharField(), default=[], read_only=True
    )

    image_url = rest_framework.serializers.URLField(source="get_image_url", read_only=True)
    icon_url = rest_framework.serializers.URLField(source="get_icon_url", read_only=True)
    ad_tag = rest_framework.serializers.CharField(read_only=True)
    video_asset_id = rest_framework.serializers.UUIDField(read_only=True)

    trackers = restapi.serializers.trackers.TrackersSerializer(read_only=True)


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
    status = restapi.serializers.fields.DashConstantField(
        dash.constants.CreativeBatchStatus, default=dash.constants.CreativeBatchStatus.IN_PROGRESS, read_only=True
    )
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


class AdTypeSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(dash.constants.AdType, required=True)


class CreativeCandidateCommonSerializer(AdTypeSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    original_creative_id = restapi.serializers.fields.IdField(read_only=True)

    url = rest_framework.serializers.URLField(required=True)
    title = restapi.serializers.fields.PlainCharField(required=True)
    display_url = rest_framework.serializers.URLField(required=True)

    tags = rest_framework.serializers.ListSerializer(child=rest_framework.serializers.CharField(), default=[])
    trackers = restapi.serializers.trackers.TrackersSerializer(allow_null=True, required=False)


# TODO (msuber): add support for icon and image
class NativeCreativeCandidateSerializer(CreativeCandidateCommonSerializer):
    brand_name = restapi.serializers.fields.PlainCharField(required=True)
    description = restapi.serializers.fields.PlainCharField(required=True)
    call_to_action = restapi.serializers.fields.PlainCharField(required=True)
    image_crop = restapi.serializers.fields.PlainCharField(required=True)


# TODO (msuber): add support for video_asset
class VideoCreativeCandidateSerializer(NativeCreativeCandidateSerializer):
    video_asset_id = rest_framework.serializers.UUIDField(required=True)


# TODO (msuber): add support for image
class ImageCreativeCandidateSerializer(CreativeCandidateCommonSerializer):
    pass


# TODO (msuber): add support for ad_tag_width, ad_tag_height
class AdTagCreativeCandidateSerializer(CreativeCandidateCommonSerializer):
    ad_tag = rest_framework.serializers.CharField(required=True)


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
