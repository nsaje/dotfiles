import rest_framework.serializers

import automation.rules
import core.models
import restapi.serializers.base
import restapi.serializers.fields


class RuleConditionMetricSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(automation.rules.MetricType, source="left_operand_type")
    window = restapi.serializers.fields.DashConstantField(automation.rules.MetricWindow, source="left_operand_window")
    modifier = rest_framework.serializers.FloatField(source="left_operand_modifier", allow_null=True)


class RuleConditionValueSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(automation.rules.ValueType, source="right_operand_type")
    window = restapi.serializers.fields.DashConstantField(automation.rules.MetricWindow, source="right_operand_window")
    value = restapi.serializers.fields.PlainCharField(
        max_length=127, error_messages={"required": "Please specify right operand value."}, source="right_operand_value"
    )


class RuleConditionSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    operator = restapi.serializers.fields.DashConstantField(automation.rules.Operator)
    metric = RuleConditionMetricSerializer(source="*")
    value = RuleConditionValueSerializer(source="*")


class RuleEntitySerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    def __init__(self, *args, level=None, queryset=None, **kwargs):
        self.fields["included"] = rest_framework.serializers.SlugRelatedField(
            source=level + "_included", queryset=queryset, required=False, many=True, slug_field="id"
        )
        # self.fields["excluded"] = rest_framework.serializers.SlugRelatedField(source=level + "_excluded", required=False, many=True, slug_field="id", read_only=True)
        super().__init__(*args, **kwargs)


class RuleEntitiesSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    ad_group = RuleEntitySerializer(
        level="ad_groups", queryset=core.models.AdGroup.objects.all(), source="*", required=False
    )
    # campaign = RuleEntitySerializer(level="campaigns", source="*", required=False)
    # account = RuleEntitySerializer(level="accounts", source="*", required=False)


class RuleSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    agency_id = restapi.serializers.fields.IdField(read_only=True)
    name = restapi.serializers.fields.PlainCharField(
        max_length=127, error_messages={"required": "Please specify rule name."}
    )

    entities = RuleEntitiesSerializer(source="*")

    target_type = restapi.serializers.fields.DashConstantField(automation.rules.TargetType)

    action_type = restapi.serializers.fields.DashConstantField(automation.rules.ActionType)
    change_step = rest_framework.serializers.FloatField()
    change_limit = rest_framework.serializers.FloatField()
    action_frequency = rest_framework.serializers.IntegerField(source="cooldown")

    notification_type = restapi.serializers.fields.DashConstantField(automation.rules.NotificationType)
    notification_recipients = rest_framework.serializers.ListSerializer(
        child=rest_framework.serializers.EmailField(), default=[], allow_empty=True
    )

    conditions = rest_framework.serializers.ListSerializer(
        child=RuleConditionSerializer(), default=[], allow_empty=True
    )
