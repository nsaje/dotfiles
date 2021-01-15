import rest_framework.serializers

import automation.rules
import core.features.publisher_groups
import core.models
import dash.constants
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers
import zemauth.access
from zemauth.features.entity_permission import Permission


class RuleConditionMetricSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    type = restapi.serializers.fields.DashConstantField(automation.rules.MetricType, source="left_operand_type")
    window = restapi.serializers.fields.DashConstantField(
        automation.rules.MetricWindow, source="left_operand_window", allow_null=True, initial=None
    )
    modifier = rest_framework.serializers.FloatField(source="left_operand_modifier", allow_null=True)
    conversion_pixel = rest_framework.serializers.PrimaryKeyRelatedField(
        queryset=core.models.ConversionPixel.objects.all(), required=False, allow_null=True
    )
    conversion_pixel_window = restapi.serializers.fields.DashConstantField(
        dash.constants.ConversionWindows, required=False, allow_null=True, initial=None
    )
    conversion_pixel_attribution = restapi.serializers.fields.DashConstantField(
        automation.rules.ConversionAttributionType, required=False, allow_null=True, initial=None
    )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret["conversion_pixel"]:
            ret["conversion_pixel"] = str(ret["conversion_pixel"])
        return ret


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


class RuleAdGroupSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(required=True)
    name = rest_framework.serializers.CharField(source="settings.ad_group_name", allow_blank=True, required=False)


class RuleCampaignSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(required=True)
    name = rest_framework.serializers.CharField(source="settings.name", allow_blank=True, required=False)


class RuleAccountSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(required=True)
    name = rest_framework.serializers.CharField(source="settings.name", allow_blank=True, required=False)


class RuleAdGroupsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    included = RuleAdGroupSerializer(source="ad_groups_included", many=True, read_only=True)

    def to_internal_value(self, instance):
        data = super().to_internal_value(instance)
        ad_groups = [
            zemauth.access.get_ad_group(self.context["request"].user, Permission.WRITE, ag.get("id"))
            for ag in instance.get("included")
        ]
        data["ad_groups_included"] = ad_groups
        return data


class RuleCampaignsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    included = RuleCampaignSerializer(source="campaigns_included", many=True, read_only=True)

    def to_internal_value(self, instance):
        data = super().to_internal_value(instance)
        campaigns = [
            zemauth.access.get_campaign(self.context["request"].user, Permission.WRITE, campaign.get("id"))
            for campaign in instance.get("included")
        ]
        data["campaigns_included"] = campaigns
        return data


class RuleAccountsSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    included = RuleAccountSerializer(source="accounts_included", many=True, read_only=True)

    def to_internal_value(self, instance):
        data = super().to_internal_value(instance)
        accounts = [
            zemauth.access.get_account(self.context["request"].user, Permission.WRITE, account.get("id"))
            for account in instance.get("included")
        ]
        data["accounts_included"] = accounts
        return data


class RuleEntitiesSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    ad_groups = RuleAdGroupsSerializer(source="*", required=False)
    campaigns = RuleCampaignsSerializer(source="*", required=False)
    accounts = RuleAccountsSerializer(source="*", required=False)


class PublisherGroupSerializer(rest_framework.serializers.ModelSerializer):
    class Meta:
        model = core.features.publisher_groups.PublisherGroup
        fields = ("id", "name", "account_id", "agency_id")

    id = restapi.serializers.fields.IdField()
    name = restapi.serializers.fields.PlainCharField(max_length=255, read_only=True)
    agency_id = restapi.serializers.fields.IdField(read_only=True)
    account_id = restapi.serializers.fields.IdField(read_only=True)


class RuleSerializer(rest_framework.serializers.Serializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    agency_id = restapi.serializers.fields.IdField(allow_null=True, required=False)
    agency_name = rest_framework.serializers.CharField(source="agency.name", default=None, read_only=True)
    account_id = restapi.serializers.fields.IdField(allow_null=True, required=False)
    account_name = rest_framework.serializers.CharField(source="account.settings.name", default=None, read_only=True)
    name = restapi.serializers.fields.PlainCharField(
        max_length=127,
        error_messages={"required": "Please specify a rule name.", "null": "Please specify a rule name."},
    )
    state = restapi.serializers.fields.DashConstantField(automation.rules.RuleState, required=False)
    archived = rest_framework.fields.BooleanField(required=False)

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

    publisher_group = PublisherGroupSerializer(required=False, allow_null=True)

    action_frequency = rest_framework.serializers.IntegerField(source="cooldown", required=False, allow_null=True)

    notification_type = restapi.serializers.fields.DashConstantField(automation.rules.NotificationType)
    notification_recipients = rest_framework.serializers.ListSerializer(
        child=restapi.serializers.fields.PlainCharField(), default=[], allow_empty=True
    )

    conditions = rest_framework.serializers.ListSerializer(
        child=RuleConditionSerializer(), default=[], allow_empty=True
    )

    window = restapi.serializers.fields.DashConstantField(automation.rules.MetricWindow, allow_null=True)

    def validate_entities(self, entities):
        if not any(
            [entities.get("accounts_included"), entities.get("campaigns_included"), entities.get("ad_groups_included")]
        ):
            raise rest_framework.serializers.ValidationError(
                ["Please specify at least one entity on which the rule should run on."]
            )
        return entities

    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        if "agency_id" in value:
            agency_id = value["agency_id"]
            value["agency"] = (
                zemauth.access.get_agency(self.context["request"].user, Permission.WRITE, agency_id)
                if agency_id
                else None
            )

        if "account_id" in value:
            account_id = value["account_id"]
            value["account"] = (
                zemauth.access.get_account(self.context["request"].user, Permission.WRITE, account_id)
                if account_id
                else None
            )

        publisher_group = value.get("publisher_group", {})
        if publisher_group:
            value["publisher_group"] = zemauth.access.get_publisher_group(
                self.context["request"].user, Permission.READ, publisher_group["id"]
            )
        return value


class RuleQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    agency_only = restapi.serializers.fields.NullBooleanField(required=False, default=False)
    keyword = restapi.serializers.fields.PlainCharField(required=False)


class RuleHistorySerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(read_only=True)
    created_dt = rest_framework.serializers.DateTimeField(read_only=True)
    status = restapi.serializers.fields.IntegerField(read_only=True)
    changes = restapi.serializers.fields.PlainCharField(read_only=True, allow_null=True)
    changes_text = rest_framework.serializers.JSONField(read_only=True, allow_null=True)
    changes_formatted = restapi.serializers.fields.PlainCharField(source="get_formatted_changes", read_only=True)
    rule_id = restapi.serializers.fields.IdField(read_only=True)
    rule_name = restapi.serializers.fields.PlainCharField(source="rule.name", read_only=True)
    ad_group_id = restapi.serializers.fields.IdField(read_only=True)
    ad_group_name = restapi.serializers.fields.PlainCharField(source="ad_group.name", read_only=True)


class RuleHistoryQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    agency_id = restapi.serializers.fields.IdField(required=False)
    account_id = restapi.serializers.fields.IdField(required=False)
    rule_id = restapi.serializers.fields.IdField(required=False)
    ad_group_id = restapi.serializers.fields.IdField(required=False)
    start_date = rest_framework.serializers.DateField(required=False)
    end_date = rest_framework.serializers.DateField(required=False)
    show_entries_without_changes = restapi.serializers.fields.NullBooleanField(required=False, default=True)
