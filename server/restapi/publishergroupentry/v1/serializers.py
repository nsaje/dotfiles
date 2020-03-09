import rest_framework.serializers

import core.features.publisher_groups
import restapi.serializers.fields
from restapi.serializers import serializers


class PublisherGroupEntrySerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin,
    serializers.DataNodeSerializerMixin,
    rest_framework.serializers.ModelSerializer,
):
    class Meta:
        model = core.features.publisher_groups.PublisherGroupEntry
        fields = ("id", "source", "publisher", "placement", "publisher_group_id", "include_subdomains")
        permissioned_fields = {"placement": "zemauth.can_use_placement_targeting"}
        list_serializer_class = serializers.DataNodeListSerializer

    id = restapi.serializers.fields.IdField(read_only=True)
    source = restapi.serializers.fields.SourceIdSlugField(required=False, allow_null=True)
    publisher = restapi.serializers.fields.PlainCharField(label="Publisher name or domain", max_length=127)
    placement = restapi.serializers.fields.PlainCharField(max_length=127, required=False, allow_null=True)
    publisher_group_id = restapi.serializers.fields.IdField(read_only=True)


class OutbrainPublisherGroupEntrySerializer(PublisherGroupEntrySerializer):
    class Meta:
        model = core.features.publisher_groups.PublisherGroupEntry
        fields = (
            "id",
            "source",
            "publisher",
            "placement",
            "publisher_group_id",
            "include_subdomains",
            "outbrain_publisher_id",
            "outbrain_section_id",
            "outbrain_amplify_publisher_id",
            "outbrain_engage_publisher_id",
        )
        permissioned_fields = {"placement": "zemauth.can_use_placement_targeting"}
        list_serializer_class = serializers.DataNodeListSerializer
