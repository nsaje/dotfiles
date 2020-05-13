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
    implicit = fields.BooleanField(required=False)


class PublisherGroupSerializer(restapi.publishergroup.v1.serializers.PublisherGroupSerializer):
    class Meta(restapi.publishergroup.v1.serializers.PublisherGroupSerializer.Meta):
        fields = restapi.publishergroup.v1.serializers.PublisherGroupSerializer.Meta.fields + (
            "include_subdomains",
            "agency_id",
            "size",
            "implicit",
            "modified_dt",
            "created_dt",
            "agency_name",
            "account_name",
            "type",
            "level",
            "level_name",
            "level_id",
        )

    agency_id = restapi.serializers.fields.IdField(read_only=True)
    include_subdomains = serializers.BooleanField(source="default_include_subdomains")
    size = serializers.IntegerField(source="entities_count", read_only=True)
    implicit = serializers.BooleanField()
    modified_dt = serializers.DateTimeField(read_only=True)
    created_dt = serializers.DateTimeField(read_only=True)
    agency_name = serializers.CharField(source="agency.name", read_only=True)
    account_name = serializers.CharField(source="account.settings.name", read_only=True)
    type = serializers.CharField()
    level = serializers.CharField()
    level_name = serializers.CharField()
    level_id = serializers.IntegerField()


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


class PublisherGroupConnectionSerializer(
    restapi.serializers.serializers.DataNodeSerializerMixin, serializers.Serializer
):
    id = restapi.serializers.fields.IdField(read_only=True)
    name = restapi.serializers.fields.PlainCharField(max_length=256)
    location = restapi.serializers.fields.PlainCharField(max_length=18)
