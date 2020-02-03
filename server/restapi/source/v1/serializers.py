import rest_framework

import restapi.serializers.base


class SourceSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    slug = rest_framework.serializers.CharField(source="bidder_slug", read_only=True)
    name = rest_framework.serializers.CharField(read_only=True)
