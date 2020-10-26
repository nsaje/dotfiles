import decimal

from rest_framework import serializers

import restapi.serializers.fields


class InternalAdGroupSourcesRealtimeStatsSpendBySourceSerializer(serializers.Serializer):
    source = restapi.serializers.fields.PlainCharField(source="source.name")
    spend = serializers.DecimalField(max_digits=20, decimal_places=2, rounding=decimal.ROUND_HALF_DOWN)


class InternalAdGroupSourcesRealtimeStatsSerializer(serializers.Serializer):
    spend = InternalAdGroupSourcesRealtimeStatsSpendBySourceSerializer(many=True)
    impressions = serializers.IntegerField()
    clicks = serializers.IntegerField()
