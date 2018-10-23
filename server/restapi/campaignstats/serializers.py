import decimal

import rest_framework.serializers


class CampaignStatsSerializer(rest_framework.serializers.Serializer):
    total_cost = rest_framework.serializers.DecimalField(
        source="local_total_cost", max_digits=20, decimal_places=2, rounding=decimal.ROUND_HALF_DOWN
    )
    impressions = rest_framework.serializers.IntegerField()
    clicks = rest_framework.serializers.IntegerField()
    cpc = rest_framework.serializers.DecimalField(
        source="local_cpc", max_digits=5, decimal_places=3, rounding=decimal.ROUND_HALF_DOWN
    )
