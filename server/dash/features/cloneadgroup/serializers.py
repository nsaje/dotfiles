from rest_framework import serializers
import restapi.fields


class CloneAdGroupSerializer(serializers.Serializer):
    ad_group_id = restapi.fields.IdField(required=True)
    destination_campaign_id = restapi.fields.IdField(required=True)


class AdGroupSerializer(serializers.Serializer):
    id = restapi.fields.IdField()
    name = serializers.ReadOnlyField()
    state = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    active = serializers.ReadOnlyField()
