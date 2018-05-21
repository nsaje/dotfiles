import rest_framework.serializers

import restapi.fields
import restapi.serializers
import restapi.serializers.base

from dash import constants


class AdGroupSourcesRTBSerializer(restapi.serializers.base.RESTAPIBaseSerializer):

    group_enabled = rest_framework.serializers.BooleanField(
        source='b1_sources_group_enabled',
    )
    state = restapi.fields.DashConstantField(
        constants.AdGroupSourceSettingsState,
        source='b1_sources_group_state'
    )
    daily_budget = restapi.fields.TwoWayBlankDecimalField(
        source='b1_sources_group_daily_budget',
        max_digits=10,
        decimal_places=4,
        output_precision=2,
    )
    cpc = rest_framework.serializers.DecimalField(
        source='b1_sources_group_cpc_cc',
        max_digits=10,
        decimal_places=4,
    )
