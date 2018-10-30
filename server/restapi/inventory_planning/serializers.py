from rest_framework import fields
from rest_framework import serializers

import restapi.serializers.fields
import restapi.serializers.serializers

COUNTRY = "country"
DEVICE_TYPE = "device_type"
PUBLISHER = "publisher"
SOURCE_ID = "source_id"
VALID_FIELDS = (None, COUNTRY, DEVICE_TYPE, PUBLISHER, SOURCE_ID)


class QueryFilter(serializers.Serializer):
    countries = fields.ListField(child=restapi.serializers.fields.PlainCharField(), required=False, source="country")
    devices = fields.ListField(child=fields.IntegerField(), required=False, source="device_type")
    publishers = fields.ListField(child=restapi.serializers.fields.PlainCharField(), required=False, source="publisher")
    sources = fields.ListField(child=fields.IntegerField(), required=False, source="source_id")


class QueryFilterGET(restapi.serializers.serializers.QueryParamsExpectations, QueryFilter):
    pass
