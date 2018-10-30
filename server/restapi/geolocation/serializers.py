from rest_framework import fields
from rest_framework import serializers

import dash.constants
import dash.features.geolocation
import restapi.serializers.fields
import restapi.serializers.serializers


class GeolocationQueryParamsExpectations(restapi.serializers.serializers.QueryParamsExpectations):
    types = fields.ListField(
        child=restapi.serializers.fields.DashConstantField(dash.constants.LocationType), max_length=10
    )
    limit = fields.IntegerField(max_value=50, default=10)
    keys = fields.ListField(child=restapi.serializers.fields.PlainCharField(), max_length=50)
    name_contains = restapi.serializers.fields.PlainCharField(min_length=2, max_length=50, required=False)


class GeolocationSerializer(serializers.ModelSerializer):
    type = restapi.serializers.fields.DashConstantField(dash.constants.LocationType)

    class Meta:
        model = dash.features.geolocation.Geolocation
        fields = ("key", "type", "name", "outbrain_id", "woeid", "facebook_key")
