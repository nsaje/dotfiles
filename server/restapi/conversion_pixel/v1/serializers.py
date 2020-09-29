import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers


class ConversionPixelSerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin, restapi.serializers.base.RESTAPIBaseSerializer
):
    class Meta:
        permissioned_fields = {"redirect_url": "zemauth.can_redirect_pixels"}

    id = restapi.serializers.fields.IdField(read_only=True)
    account_id = restapi.serializers.fields.IdField(read_only=True)
    name = restapi.serializers.fields.PlainCharField(read_only=True)
    archived = rest_framework.serializers.BooleanField(required=False)
    audience_enabled = rest_framework.serializers.ReadOnlyField(default=True)
    url = rest_framework.serializers.URLField(source="get_url", read_only=True)
    redirect_url = rest_framework.serializers.URLField(
        max_length=2048, required=False, allow_blank=True, allow_null=True
    )
    notes = restapi.serializers.fields.PlainCharField(required=False, allow_blank=True)
    last_triggered = rest_framework.serializers.DateTimeField(read_only=True)
    impressions = rest_framework.serializers.IntegerField(source="get_impressions", read_only=True)


class ConversionPixelCreateSerializer(ConversionPixelSerializer):
    name = restapi.serializers.fields.PlainCharField(
        max_length=50, error_messages={"required": "Please specify a name."}
    )
