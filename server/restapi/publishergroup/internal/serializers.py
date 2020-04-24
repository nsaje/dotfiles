from rest_framework import fields
from rest_framework import serializers

import restapi.publishergroup.v1.serializers
import restapi.publishergroupentry.v1.serializers
import restapi.serializers.fields
import restapi.serializers.serializers


class PublisherGroupQueryParamsExpectations(restapi.serializers.serializers.QueryParamsExpectations):
    keyword = restapi.serializers.fields.PlainCharField(max_length=50, required=False)
    limit = fields.IntegerField(max_value=50, default=10)
    offset = fields.IntegerField(default=0)
    agency_id = restapi.serializers.fields.IdField(default=None)
    account_id = restapi.serializers.fields.IdField(default=None)
    include_implicit = fields.BooleanField(default=True)


class PublisherGroupSerializer(restapi.publishergroup.v1.serializers.PublisherGroupSerializer):
    class Meta(restapi.publishergroup.v1.serializers.PublisherGroupSerializer.Meta):
        fields = restapi.publishergroup.v1.serializers.PublisherGroupSerializer.Meta.fields + (
            "include_subdomains",
            "agency_id",
        )

    agency_id = restapi.serializers.fields.IdField(read_only=True)
    # TODO temporary renaming field for easier front-end migration
    include_subdomains = serializers.BooleanField(source="default_include_subdomains")


class AddToPublisherGroupSerializer(restapi.publishergroup.v1.serializers.PublisherGroupSerializer):
    class Meta(restapi.publishergroup.v1.serializers.PublisherGroupSerializer.Meta):
        fields = restapi.publishergroup.v1.serializers.PublisherGroupSerializer.Meta.fields + (
            "agency_id",
            "default_include_subdomains",
            "entries",
        )

    id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    agency_id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    account_id = restapi.serializers.fields.IdField(required=False, allow_null=True)
    entries = restapi.publishergroupentry.v1.serializers.PublisherGroupEntrySerializer(many=True)

    def validate_entries(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("At least one entry is required")
        return value
