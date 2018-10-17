import decimal

import rest_framework.serializers

import restapi.serializers.fields
import restapi.serializers.base

from dash import constants


class AdGroupSourcesRTBSerializer(restapi.serializers.base.RESTAPIBaseSerializer):

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
