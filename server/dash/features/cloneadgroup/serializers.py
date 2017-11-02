from rest_framework import serializers
import restapi.fields

from dash import constants


class CloneAdGroupSerializer(serializers.Serializer):
    ad_group_id = restapi.fields.IdField(required=True)
    destination_campaign_id = restapi.fields.IdField(required=True, error_messages={
        'required': 'Please select destination campaign',
        'null': 'Please select destination campaign',
    })
    destination_ad_group_name = restapi.fields.PlainCharField(required=True, error_messages={
        'required': 'Please provide a name for destination ad group',
        'blank': 'Please provide a name for destination ad group',
    })
    clone_ads = serializers.BooleanField(required=False)


class AdGroupSerializer(serializers.Serializer):
    id = restapi.fields.IdField()
    campaign_id = restapi.fields.IdField()
    name = serializers.ReadOnlyField()

    state = restapi.fields.DashConstantField(constants.AdGroupSettingsState)
    status = restapi.fields.DashConstantField(constants.AdGroupRunningStatus)
    active = restapi.fields.DashConstantField(constants.InfoboxStatus)
