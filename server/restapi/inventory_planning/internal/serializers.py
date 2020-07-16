from rest_framework import fields
from rest_framework import serializers

import restapi.serializers.fields
import restapi.serializers.serializers


class QueryFilter(serializers.Serializer):
    countries = fields.ListField(child=restapi.serializers.fields.PlainCharField(), required=False, source="country")
    devices = fields.ListField(child=fields.IntegerField(), required=False, source="device_type")
    publishers = fields.ListField(child=restapi.serializers.fields.PlainCharField(), required=False, source="publisher")
    sources = fields.ListField(child=fields.IntegerField(), required=False, source="source_id")
    channels = fields.ListField(child=restapi.serializers.fields.PlainCharField(), required=False, source="channel")


class QueryFilterGET(restapi.serializers.serializers.QueryParamsExpectations, QueryFilter):
    pass
