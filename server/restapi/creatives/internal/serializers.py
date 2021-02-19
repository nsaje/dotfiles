import rest_framework.serializers

import core.features.videoassets.models
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

    hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    landscape_hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    portrait_hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    display_hosted_image_url = rest_framework.serializers.URLField(read_only=True)
    hosted_icon_url = rest_framework.serializers.URLField(read_only=True)
    image_width = rest_framework.serializers.CharField(source="image.width", read_only=True)
    image_height = rest_framework.serializers.CharField(source="image.height", read_only=True)
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

        if "video_asset_id" in value.keys():
            value["video_asset"] = self.to_internal_value_video_asset(value["video_asset_id"])

        return value

    # TODO (msuber): add video asset scope validation
    def to_internal_value_video_asset(self, data):
        if data is None:
            return data
        return core.features.videoassets.models.VideoAsset.objects.get(pk=data)


class ImageCreativeCandidateSerializer(CreativeCandidateCommonSerializer):
    image_url = rest_framework.serializers.URLField(required=False)
    image = rest_framework.serializers.ImageField(max_length=1024, allow_empty_file=False, required=False)


class AdTagCreativeCandidateSerializer(CreativeCandidateCommonSerializer):
    image_width = rest_framework.serializers.IntegerField(required=True)
    image_height = rest_framework.serializers.IntegerField(required=True)
    ad_tag = rest_framework.serializers.CharField(required=True)

    def validate_image_width(self, value):
        supported_widths = [s[0] for s in dash.constants.DisplayAdSize.get_all()]
        if all(value != width for width in supported_widths):
            widths = ", ".join([str(w) for w in supported_widths])
            raise rest_framework.serializers.ValidationError(
                ["Image width invalid. Supported widths are: {widths}".format(widths=widths)]
            )
        return value

    def validate_image_height(self, value):
        supported_heights = [s[1] for s in dash.constants.DisplayAdSize.get_all()]
        if all(value != height for height in supported_heights):
            heights = ", ".join([str(h) for h in supported_heights])
            raise rest_framework.serializers.ValidationError(
                ["Image height invalid. Supported heights are: {heights}".format(heights=heights)]
            )
        return value

    def validate(self, value):
        self._validate_ad_size(value.get("image_width"), value.get("image_height"))
        return value

    @staticmethod
    def _validate_ad_size(width, height):
        if not width and not height:
            return
        supported_sizes = dash.constants.DisplayAdSize.get_all()
        if all(width != size[0] or height != size[1] for size in supported_sizes):
            sizes = ", ".join([str(s[0]) + "x" + str(s[1]) for s in supported_sizes])
            raise rest_framework.serializers.ValidationError(
                "Ad size invalid. Supported sizes are (width x height): {sizes}".format(sizes=sizes)
            )


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
