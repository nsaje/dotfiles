import decimal
from decimal import Decimal

import rest_framework.serializers

import restapi.serializers.base
import restapi.serializers.fields
from dash import constants


class CampaignGoalsDefaultsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    def to_representation(self, obj):
        return {constants.CampaignGoalKPI.get_name(k): v for k, v in obj.items()}


class ConversionGoalSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    def run_validation(self, data):
        if data is None:
            return {}
        return super().run_validation(data)

    def to_representation(self, goal):
        if goal.conversion_goal is None:
            return None
        if goal.conversion_goal.pixel_id:
            self.fields["goal_id"] = restapi.serializers.fields.PlainCharField(
                source="conversion_goal.pixel_id", allow_blank=True, allow_null=True
            )
        self.fields["conversion_window"] = restapi.serializers.fields.OutNullDashConstantField(
            constants.ConversionWindowsLegacy, source="conversion_goal.conversion_window"
        )
        return super().to_representation(goal)

    goal_id = restapi.serializers.fields.PlainCharField(
        source="conversion_goal.goal_id",
        max_length=100,
        allow_blank=True,
        allow_null=True,
        error_messages={"max_length": "Conversion goal id is too long."},
    )
    name = restapi.serializers.fields.PlainCharField(
        source="conversion_goal.name", max_length=100, allow_blank=True, allow_null=True, required=False
    )
    type = restapi.serializers.fields.DashConstantField(constants.ConversionGoalType, source="conversion_goal.type")
    conversion_window = restapi.serializers.fields.OutNullDashConstantField(
        constants.ConversionWindows, source="conversion_goal.conversion_window"
    )
    pixel_url = restapi.serializers.fields.OutNullURLField(
        source="conversion_goal.pixel.get_url", max_length=2048, allow_blank=True, allow_null=True, read_only=True
    )


class CampaignGoalSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.OutIntIdField(required=False, allow_null=True)
    type = restapi.serializers.fields.DashConstantField(constants.CampaignGoalKPI)
    primary = rest_framework.serializers.BooleanField()
    value = rest_framework.serializers.DecimalField(max_digits=20, decimal_places=5, rounding=decimal.ROUND_HALF_DOWN)
    conversion_goal = ConversionGoalSerializer(source="*", allow_null=True, required=False)

    def to_representation(self, instance):
        self.fields["value"] = rest_framework.serializers.SerializerMethodField()
        return super().to_representation(instance)

    def get_value(self, goal):
        value = goal.get_current_value()
        if not value:
            return value
        rounding_format = "1.000" if goal.type == constants.CampaignGoalKPI.CPC else "1.00"
        return Decimal(value.local_value).quantize(Decimal(rounding_format))
