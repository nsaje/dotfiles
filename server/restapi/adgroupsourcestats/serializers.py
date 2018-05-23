from rest_framework import serializers

import restapi.serializers.fields


class AdGroupSourcesRealtimeStatsSerializer(serializers.Serializer):
    source = restapi.serializers.fields.PlainCharField(source='source.name')
    spend = serializers.DecimalField(max_digits=20, decimal_places=2)
