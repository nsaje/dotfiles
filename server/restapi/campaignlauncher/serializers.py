from rest_framework import serializers
from rest_framework import fields

import dash.constants
import restapi.fields


class ConversionGoalSerializer(serializers.Serializer):
    type = restapi.fields.DashConstantField(dash.constants.ConversionGoalType)
    conversion_window = restapi.fields.DashConstantField(dash.constants.ConversionWindows, required=False)
    goal_id = serializers.CharField(
        max_length=100,
        error_messages={
            'max_length': 'Conversion goal id is too long (%(show_value)d/%(limit_value)d).',
        }
    )


class CampaignGoalSerializer(serializers.Serializer):
    type = restapi.fields.DashConstantField(dash.constants.CampaignGoalKPI)
    value = fields.DecimalField(max_digits=15, decimal_places=5)
    conversion_goal = ConversionGoalSerializer()


class CampaignLauncherSerializer(serializers.Serializer):
    campaign_name = fields.CharField(
        max_length=127,
        error_messages={'required': 'Please specify campaign name.'}
    )
    iab_category = restapi.fields.DashConstantField(
        dash.constants.IABCategory,
        error_messages={'required': 'Please specify the IAB category.'}
    )
    start_date = fields.DateField()
    end_date = fields.DateField()
    budget_amount = fields.IntegerField(min_value=0)
    goal = CampaignGoalSerializer()
