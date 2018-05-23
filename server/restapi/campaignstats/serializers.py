import rest_framework.serializers


class CampaignStatsSerializer(rest_framework.serializers.Serializer):
    total_cost = rest_framework.serializers.DecimalField(20, 2)
    impressions = rest_framework.serializers.IntegerField()
    clicks = rest_framework.serializers.IntegerField()
    cpc = rest_framework.serializers.DecimalField(5, 3)
