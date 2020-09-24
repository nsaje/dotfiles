import decimal

import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
from dash import constants


class AdGroupSourcesRTBSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    class Meta:
        permissioned_fields = {}

    @property
    def fields(self):
        fields = super().fields
        ad_group = self.context.get("ad_group")
        if ad_group and ad_group.bidding_type == constants.BiddingType.CPM:
            fields["cpc"].allow_null = True
        elif "cpm" in fields:
            fields["cpm"].allow_null = True
        return fields

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ad_group = self.context.get("ad_group")
        if ad_group and ad_group.bidding_type == constants.BiddingType.CPM:
            ret["cpc"] = None
        elif "cpm" in ret:
            ret["cpm"] = None
        return ret

    group_enabled = rest_framework.serializers.BooleanField(source="b1_sources_group_enabled")
    state = restapi.serializers.fields.DashConstantField(
        constants.AdGroupSourceSettingsState, source="b1_sources_group_state"
    )
    daily_budget = restapi.serializers.fields.TwoWayBlankDecimalField(
        source="local_b1_sources_group_daily_budget",
        max_digits=10,
        decimal_places=4,
        output_precision=2,
        rounding=decimal.ROUND_HALF_DOWN,
    )
    cpc = rest_framework.serializers.DecimalField(
        source="local_b1_sources_group_cpc_cc", max_digits=10, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN
    )
    cpm = rest_framework.serializers.DecimalField(
        source="local_b1_sources_group_cpm", max_digits=10, decimal_places=4, rounding=decimal.ROUND_HALF_DOWN
    )
