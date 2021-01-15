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

    name = rest_framework.serializers.CharField(max_length=1024, allow_null=False, allow_blank=False, required=True)
    status = restapi.serializers.fields.DashConstantField(
        dash.constants.CreativeBatchStatus, default=dash.constants.CreativeBatchStatus.IN_PROGRESS, read_only=True
    )

    tags = rest_framework.serializers.ListSerializer(child=rest_framework.serializers.CharField(), default=[])
    image_crop = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)
    display_url = rest_framework.serializers.URLField(allow_null=True, required=False)
    brand_name = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)
    description = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)
    call_to_action = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)

    created_by = rest_framework.serializers.EmailField(read_only=True)
    created_dt = rest_framework.serializers.DateTimeField(read_only=True)
