import decimal

from rest_framework import fields
from rest_framework import serializers

import realtimeapi.constants
import restapi.serializers.fields
import restapi.serializers.serializers


class RealtimeStatsSerializer(serializers.Serializer):
    account_id = serializers.IntegerField(required=False)
    campaign_id = serializers.IntegerField(required=False)
    ad_group_id = serializers.IntegerField(required=False)
    content_ad_id = serializers.IntegerField(required=False)
    publisher = serializers.IntegerField(required=False)
    device_type = serializers.IntegerField(required=False)

    spend = serializers.DecimalField(max_digits=20, decimal_places=2, rounding=decimal.ROUND_HALF_DOWN)
    clicks = serializers.IntegerField()
    impressions = serializers.IntegerField()
    ctr = serializers.DecimalField(max_digits=20, decimal_places=3, rounding=decimal.ROUND_HALF_DOWN)
    cpc = serializers.DecimalField(max_digits=20, decimal_places=3, rounding=decimal.ROUND_HALF_DOWN)
    cpm = serializers.DecimalField(max_digits=20, decimal_places=3, rounding=decimal.ROUND_HALF_DOWN)


class BaseQueryParamsExpectations(restapi.serializers.serializers.QueryParamsExpectations):
    campaign_id = restapi.serializers.fields.IdField(required=False)
    ad_group_id = restapi.serializers.fields.IdField(required=False)
    content_ad_id = restapi.serializers.fields.IdField(required=False)


class GroupByQueryParamsExpectations(BaseQueryParamsExpectations):
    account_id = restapi.serializers.fields.IdField(required=False)
    limit = fields.IntegerField(max_value=100, default=10)
    marker = restapi.serializers.fields.IdField(default=None)
    breakdown = restapi.serializers.fields.ChoiceField(
        choices=realtimeapi.constants.ValidGroupByBreakdown.get_all(), required=False
    )


class TopNQueryParamsExpectations(BaseQueryParamsExpectations):
    breakdown = restapi.serializers.fields.ChoiceField(
        choices=realtimeapi.constants.ValidTopNBreakdown.get_all(), required=False
    )
    order = restapi.serializers.fields.OrderChoiceField(
        choices=realtimeapi.constants.ValidOrder.get_all(), required=False
    )
