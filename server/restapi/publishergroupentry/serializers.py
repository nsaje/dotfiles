from restapi.serializers import serializers
import restapi.serializers.fields

import rest_framework.serializers
import core.features.publisher_groups


class PublisherGroupEntrySerializer(serializers.DataNodeSerializerMixin, rest_framework.serializers.ModelSerializer):
    class Meta:
        model = core.features.publisher_groups.PublisherGroupEntry
        fields = ("id", "publisher", "publisher_group_id", "source", "include_subdomains")
        list_serializer_class = serializers.DataNodeListSerializer

    id = restapi.serializers.fields.IdField(read_only=True)
    publisher = restapi.serializers.fields.PlainCharField(label="Publisher name or domain", max_length=127)
    publisher_group_id = restapi.serializers.fields.IdField(read_only=True)
    source = restapi.serializers.fields.SourceIdSlugField(required=False, allow_null=True)


class OutbrainPublisherGroupEntrySerializer(PublisherGroupEntrySerializer):
    class Meta:
        model = core.features.publisher_groups.PublisherGroupEntry
        fields = (
            "id",
            "publisher",
            "publisher_group_id",
            "source",
            "include_subdomains",
            "outbrain_publisher_id",
            "outbrain_section_id",
            "outbrain_amplify_publisher_id",
            "outbrain_engage_publisher_id",
        )
        list_serializer_class = serializers.DataNodeListSerializer
