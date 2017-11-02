from rest_framework import serializers

import restapi.fields
import dash.constants
import dash.views.publishers


class PublisherSerializer(serializers.Serializer):
    name = restapi.fields.PlainCharField(max_length=127)
    source = restapi.fields.SourceIdSlugField(required=False, allow_null=True)
    status = restapi.fields.DashConstantField(dash.constants.PublisherStatus)
    level = restapi.fields.DashConstantField(dash.constants.PublisherBlacklistLevel, label='level')
    modifier = serializers.FloatField(min_value=0.01, max_value=7.0, required=False, allow_null=True)
