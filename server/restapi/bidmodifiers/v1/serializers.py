from rest_framework import serializers

import restapi.serializers.fields
from core.features.bid_modifiers import constants
from core.features.bid_modifiers import helpers


class BidModifierSerializer(serializers.Serializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    type = restapi.serializers.fields.DashConstantField(constants.BidModifierType)
    source_slug = restapi.serializers.fields.PlainCharField(required=False, allow_null=True, allow_blank=True)
    target = restapi.serializers.fields.PlainCharField(max_length=127)
    modifier = serializers.FloatField(min_value=helpers.MODIFIER_MIN, max_value=helpers.MODIFIER_MAX, allow_null=True)


class BidModifierIdSerializer(serializers.Serializer):
    id = restapi.serializers.fields.IdField()
