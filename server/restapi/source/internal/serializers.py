import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields


class SourceSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    slug = rest_framework.serializers.CharField(source="bidder_slug", read_only=True)
    name = rest_framework.serializers.CharField(read_only=True)
    released = rest_framework.serializers.BooleanField(read_only=True)
    deprecated = rest_framework.serializers.BooleanField(read_only=True)
