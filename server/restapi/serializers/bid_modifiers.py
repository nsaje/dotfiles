import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
from core.features.bid_modifiers import constants


class BidModifierTypeSummary(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(constants.BidModifierType)
    count = rest_framework.serializers.IntegerField()
    min = rest_framework.serializers.FloatField()
    max = rest_framework.serializers.FloatField()
