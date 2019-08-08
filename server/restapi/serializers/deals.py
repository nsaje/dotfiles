import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
from core.features.deals import DirectDeal
from core.features.deals import DirectDealConnection


class DirectDealSerializer(rest_framework.serializers.ModelSerializer):
    class Meta:
        model = DirectDeal
        fields = "__all__"


class DirectDealConnectionSerializer(rest_framework.serializers.Serializer):
    class Meta:
        model = DirectDealConnection

    id = restapi.serializers.fields.IdField(allow_null=True)
    source = rest_framework.serializers.StringRelatedField(allow_null=True)
    exclusive = rest_framework.serializers.BooleanField()
    agency = restapi.serializers.fields.IdField(source="agency.id", allow_null=True)
    account = restapi.serializers.fields.IdField(source="account.id", allow_null=True)
    campaign = restapi.serializers.fields.IdField(source="campaign.id", allow_null=True)
    adgroup = restapi.serializers.fields.IdField(source="adgroup.id", allow_null=True)
    deals = DirectDealSerializer(many=True, required=True)
    level = rest_framework.serializers.CharField()


class DealSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    level = rest_framework.serializers.CharField(required=False)
    direct_deal_connection_id = restapi.serializers.fields.IdField(required=False)
    deal_id = rest_framework.serializers.CharField(required=False)
    source = rest_framework.serializers.CharField(required=False)
    exclusive = rest_framework.serializers.BooleanField(default=False, required=False)
    description = rest_framework.serializers.CharField(required=False)
    is_applied = rest_framework.serializers.BooleanField(default=False, required=False)
