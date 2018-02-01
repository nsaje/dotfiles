import decimal
from rest_framework import serializers
from rest_framework import fields

import dash.constants
import restapi.fields
from restapi.serializers import targeting


class ConversionGoalSerializer(serializers.Serializer):
    type = restapi.fields.DashConstantField(dash.constants.ConversionGoalType)
    conversion_window = restapi.fields.DashConstantField(dash.constants.ConversionWindows, required=False)
    goal_id = restapi.fields.PlainCharField(
        required=True,
        max_length=100,
        error_messages={
            'max_length': 'Conversion goal id is too long (%(show_value)d/%(limit_value)d).',
        }
    )


class CampaignGoalSerializer(serializers.Serializer):
    type = restapi.fields.DashConstantField(dash.constants.CampaignGoalKPI)
    value = fields.DecimalField(max_digits=15, decimal_places=5)
    conversion_goal = ConversionGoalSerializer(required=False, allow_null=True)


class CampaignLauncherSerializer(serializers.Serializer):
    campaign_name = restapi.fields.PlainCharField(
        max_length=127,
        error_messages={'required': 'Please specify campaign name.'}
    )
    iab_category = restapi.fields.DashConstantField(
        dash.constants.IABCategory,
        error_messages={'required': 'Please specify the IAB category.'}
    )
    language = restapi.fields.DashConstantField(
        dash.constants.Language,
        error_messages={'required': 'Please specify the language of the campaign\'s ads.'}
    )
    budget_amount = fields.IntegerField(min_value=0)
    max_cpc = fields.DecimalField(
        required=False,
        allow_null=True,
        max_digits=None,
        decimal_places=4,
        min_value=decimal.Decimal('0.05'),
        max_value=decimal.Decimal('10'),
        error_messages={
            'min_value': 'Maximum CPC can\'t be lower than $0.05.',
            'max_value': 'Maximum CPC can\'t be higher than $10.00.'
        }
    )
    daily_budget = fields.DecimalField(max_digits=10, decimal_places=4)
    upload_batch = restapi.fields.IdField()
    campaign_goal = CampaignGoalSerializer()
    target_regions = targeting.TargetRegionsSerializer()
    exclusion_target_regions = targeting.TargetRegionsSerializer()
    target_devices = targeting.DevicesSerializer()
    target_placements = targeting.PlacementsSerializer()
    target_os = targeting.OSsSerializer()
