import rest_framework.serializers

import restapi.serializers.fields
import restapi.serializers.serializers


class TrafficDataSerializer(rest_framework.serializers.Serializer):
    latest_complete_date = rest_framework.serializers.DateField(read_only=True)


class BooksClosedSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    traffic_data = TrafficDataSerializer(read_only=True)
