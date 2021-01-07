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
    agency_name = rest_framework.serializers.CharField(source="agency.name", read_only=True)
    account_id = restapi.serializers.fields.IdField(allow_null=True, read_only=True)
    account_name = rest_framework.serializers.CharField(source="account.settings.name", read_only=True)

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
