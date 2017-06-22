from rest_framework import serializers

from restapi import fields

from dash import constants


class AdGroupSourceSerializer(serializers.Serializer):
    source = fields.SourceIdSlugField(source='ad_group_source.source')
    cpc = serializers.DecimalField(max_digits=10, decimal_places=4, source='cpc_cc', required=False)
    daily_budget = serializers.DecimalField(max_digits=10, decimal_places=4, source='daily_budget_cc', required=False)
    state = fields.DashConstantField(constants.AdGroupSourceSettingsState, required=False)
