from rest_framework import serializers

import restapi.serializers.fields
from core.features.bid_modifiers import constants
from core.features.bid_modifiers import converters
from core.features.bid_modifiers import exceptions
from core.features.bid_modifiers import helpers
from utils import exc


class BidModifierSerializer(serializers.Serializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    type = restapi.serializers.fields.DashConstantField(constants.BidModifierType)
    source_slug = restapi.serializers.fields.PlainCharField(required=False, allow_null=True, allow_blank=True)
    target = restapi.serializers.fields.PlainCharField(max_length=127)
    modifier = serializers.FloatField(min_value=helpers.MODIFIER_MIN, max_value=helpers.MODIFIER_MAX, allow_null=True)

    def validate(self, data):
        if self.partial:
            if not self.instance:
                raise exc.ValidationError("Bid Modifier does not exist")

            for attr in ("id", "type", "source_slug", "target"):
                if attr in data:
                    if attr == "target":
                        if data[attr] != converters.ApiConverter.from_target(self.instance.type, self.instance.target):
                            raise exc.ValidationError("Only modifier field can be updated")
                    else:
                        if data[attr] != getattr(self.instance, attr):
                            raise exc.ValidationError("Only modifier field can be updated")

            if "modifier" not in data:
                raise exc.ValidationError("Modifier field is required")

            return {"modifier": data["modifier"]}

        try:
            data["target"] = converters.ApiConverter.to_target(data["type"], data["target"])
        except (exceptions.BidModifierTargetInvalid, exceptions.BidModifierUnsupportedTarget) as e:
            raise serializers.ValidationError(str(e))

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["target"] = converters.ApiConverter.from_target(instance.type, instance.target)
        return data


class BidModifierIdSerializer(serializers.Serializer):
    id = restapi.serializers.fields.IdField()
