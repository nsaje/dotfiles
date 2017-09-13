from rest_framework import serializers

import restapi.fields
import dash.constants
import dash.views.publishers


class PublisherSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=127)
    source = restapi.fields.SourceIdSlugField(required=False, allow_null=True)
    externalId = serializers.CharField(max_length=127, required=False, allow_null=True)
    status = restapi.fields.DashConstantField(dash.constants.PublisherStatus)
    level = restapi.fields.DashConstantField(dash.constants.PublisherBlacklistLevel, label='level')
