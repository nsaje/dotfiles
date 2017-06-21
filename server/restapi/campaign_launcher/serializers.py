from rest_framework import serializers
from rest_framework import fields

import dash.constants
import restapi.fields


class CampaignLauncherSerializer(serializers.Serializer):
    campaign_name = fields.CharField(
        max_length=127,
        error_messages={'required': 'Please specify campaign name.'}
    )
    iab_category = restapi.fields.DashConstantField(
        dash.constants.IABCategory,
        error_messages={'required': 'Please specify the IAB category.'}
    )
