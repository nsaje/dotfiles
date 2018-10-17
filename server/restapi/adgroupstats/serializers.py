import decimal

from rest_framework import serializers


class AdGroupRealtimeStatsSerializer(serializers.Serializer):
    spend = serializers.DecimalField(max_digits=20, decimal_places=2, rounding=decimal.ROUND_HALF_DOWN)
    clicks = serializers.IntegerField()
