from rest_framework import serializers
from rest_framework import fields

import restapi.common.serializers
import restapi.fields


COUNTRY = 'country'
DEVICE_TYPE = 'device_type'
PUBLISHER = 'publisher'
SOURCE_ID = 'source_id'
VALID_FIELDS = (None, COUNTRY, DEVICE_TYPE, PUBLISHER, SOURCE_ID)


class QueryFilter(serializers.Serializer):
    c = fields.ListField(child=restapi.fields.PlainCharField(), required=False, source='country')
    d = fields.ListField(child=fields.IntegerField(), required=False, source='device_type')
    p = fields.ListField(child=restapi.fields.PlainCharField(), required=False, source='publisher')
    s = fields.ListField(child=fields.IntegerField(), required=False, source='source_id')


class QueryFilterGET(restapi.common.serializers.QueryParamsExpectations, QueryFilter):
    pass
