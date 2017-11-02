from rest_framework import serializers
from rest_framework import fields

import dash.features.geolocation
import dash.constants
import restapi.fields
import restapi.serializers
import restapi.common.serializers


class GeolocationQueryParamsExpectations(restapi.common.serializers.QueryParamsExpectations):
    types = fields.ListField(
        child=restapi.fields.DashConstantField(dash.constants.LocationType),
        max_length=10,
    )
    limit = fields.IntegerField(max_value=50, default=10)
    keys = fields.ListField(child=restapi.fields.PlainCharField(), max_length=50)
    name_contains = restapi.fields.PlainCharField(min_length=2, max_length=50, required=False)


class GeolocationSerializer(serializers.ModelSerializer):
    type = restapi.fields.DashConstantField(dash.constants.LocationType)

    class Meta:
        model = dash.features.geolocation.Geolocation
        fields = ('key', 'type', 'name', 'outbrain_id', 'woeid', 'facebook_key')
