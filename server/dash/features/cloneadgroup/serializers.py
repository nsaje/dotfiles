from rest_framework import serializers
import restapi.fields

import core.entity


class CloneAdGroupSerializer(serializers.Serializer):
    ad_group_id = restapi.fields.IdField(required=True)
    destination_campaign_id = restapi.fields.IdField(required=True)


class AdGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = core.entity.AdGroup
        fields = ('id', 'name', 'campaign_id')

    id = restapi.fields.IdField()
    campaign_id = restapi.fields.IdField()
