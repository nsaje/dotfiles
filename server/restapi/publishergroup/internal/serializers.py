from rest_framework import fields

import restapi.publishergroup.v1.serializers
import restapi.serializers.fields
import restapi.serializers.serializers


class PublisherGroupQueryParamsExpectations(restapi.serializers.serializers.QueryParamsExpectations):
    keyword = restapi.serializers.fields.PlainCharField(max_length=50, required=False)
    limit = fields.IntegerField(max_value=50, default=10)
    offset = fields.IntegerField(default=0)


class PublisherGroupSerializer(restapi.publishergroup.v1.serializers.PublisherGroupSerializer):
    class Meta(restapi.publishergroup.v1.serializers.PublisherGroupSerializer.Meta):
        fields = restapi.publishergroup.v1.serializers.PublisherGroupSerializer.Meta.fields + ("agency_id",)

    agency_id = restapi.serializers.fields.IdField(read_only=True)
