from rest_framework import serializers
import restapi.serializers.fields

from dash import constants


class CloneAdGroupSerializer(serializers.Serializer):
    ad_group_id = restapi.serializers.fields.IdField(required=True)
    destination_campaign_id = restapi.serializers.fields.IdField(
        required=True,
        error_messages={"required": "Please select destination campaign", "null": "Please select destination campaign"},
    )
    destination_ad_group_name = restapi.serializers.fields.PlainCharField(
        required=True,
        error_messages={
            "required": "Please provide a name for destination ad group",
            "blank": "Please provide a name for destination ad group",
        },
        max_length=127,
    )
    clone_ads = serializers.BooleanField(required=False)


class AdGroupSerializer(serializers.Serializer):
    id = restapi.serializers.fields.IdField()
    campaign_id = restapi.serializers.fields.IdField()
    name = serializers.ReadOnlyField()

    state = restapi.serializers.fields.DashConstantField(constants.AdGroupSettingsState)
    status = restapi.serializers.fields.DashConstantField(constants.AdGroupRunningStatus)
    active = restapi.serializers.fields.DashConstantField(constants.InfoboxStatus)
