from rest_framework import serializers

import restapi.fields


class AdGroupRealtimeStatsSerializer(serializers.Serializer):
    spend = serializers.DecimalField(max_digits=20, decimal_places=2)
    clicks = serializers.IntegerField()


class AdGroupSourcesRealtimeStatsSerializer(serializers.Serializer):
    source = restapi.fields.PlainCharField(source='source.name')
    spend = serializers.DecimalField(max_digits=20, decimal_places=2)
