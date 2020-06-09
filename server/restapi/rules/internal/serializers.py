import rest_framework.serializers

import automation.rules
import core.features.publisher_groups
import core.models
import restapi.serializers.base
import restapi.serializers.fields
import zemauth.access
from zemauth.features.entity_permission import Permission


class RuleConditionMetricSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(automation.rules.MetricType, source="left_operand_type")
    window = restapi.serializers.fields.DashConstantField(
        automation.rules.MetricWindow, source="left_operand_window", allow_null=True
    )
    modifier = rest_framework.serializers.FloatField(source="left_operand_modifier", allow_null=True)


class RuleConditionValueSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(automation.rules.ValueType, source="right_operand_type")
    window = restapi.serializers.fields.DashConstantField(
        automation.rules.MetricWindow, source="right_operand_window", required=False, initial=None, allow_null=True
    )
    value = restapi.serializers.fields.PlainCharField(
        max_length=127,
        error_messages={"required": "Please specify a right operand value."},
        source="right_operand_value",
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
        max_length=127,
        error_messages={"required": "Please specify a rule name.", "null": "Please specify a rule name."},
    )

    entities = RuleEntitiesSerializer(source="*")

    target_type = restapi.serializers.fields.DashConstantField(
        automation.rules.TargetType,
        error_messages={"required": "Please specify a target type.", "null": "Please specify a target type."},
    )
    action_type = restapi.serializers.fields.DashConstantField(
        automation.rules.ActionType,
        error_messages={"required": "Please specify an action type.", "null": "Please specify an action type."},
    )

    change_step = rest_framework.serializers.FloatField(required=False, allow_null=True)
    change_limit = rest_framework.serializers.FloatField(required=False, allow_null=True)

    send_email_subject = restapi.serializers.fields.PlainCharField(required=False, allow_null=True, initial=None)
    send_email_body = restapi.serializers.fields.PlainCharField(required=False, allow_null=True, initial=None)
    send_email_recipients = rest_framework.serializers.ListSerializer(
        child=restapi.serializers.fields.PlainCharField(), default=[], allow_empty=True, required=False, initial=None
    )

    publisher_group_id = rest_framework.serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=core.features.publisher_groups.PublisherGroup.objects.all(),
        source="publisher_group",
    )

    action_frequency = rest_framework.serializers.IntegerField(source="cooldown", required=False, allow_null=True)

    notification_type = restapi.serializers.fields.DashConstantField(automation.rules.NotificationType)
    notification_recipients = rest_framework.serializers.ListSerializer(
        child=restapi.serializers.fields.PlainCharField(), default=[], allow_empty=True
    )

    conditions = rest_framework.serializers.ListSerializer(
        child=RuleConditionSerializer(), default=[], allow_empty=True
    )

    window = restapi.serializers.fields.DashConstantField(automation.rules.MetricWindow, allow_null=True)

    def validate_publisher_group_id(self, publisher_group):
        if publisher_group:
            user = self.context["request"].user
            zemauth.access.get_publisher_group(user, Permission.WRITE, publisher_group.id)
        return publisher_group
