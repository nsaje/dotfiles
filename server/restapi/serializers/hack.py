import rest_framework.serializers

import restapi.serializers.base


class HackSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    summary = rest_framework.serializers.CharField(required=False)
    source = rest_framework.serializers.CharField(required=False)
    level = rest_framework.serializers.CharField(required=False)
    details = rest_framework.serializers.CharField(required=False)
    confirmed = rest_framework.serializers.BooleanField(default=False, required=False)
