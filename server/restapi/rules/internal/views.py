import rest_framework.permissions
import rest_framework.serializers

import automation.rules
import restapi.access
import utils.exc
from restapi.common.pagination import StandardPagination

from . import serializers


class CanUseAutomationRulesPermission(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.fea_can_create_automation_rules"))


class RuleViewSet(restapi.campaign.v1.views.CampaignViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated, CanUseAutomationRulesPermission)

    def get(self, request, agency_id, rule_id):
        agency = restapi.access.get_agency(request.user, agency_id)
        rule = agency.rule_set.get(id=rule_id)
        serializer = serializers.RuleSerializer(rule, context={"request": request})
        return self.response_ok(data=serializer.data)

    def create(self, request, agency_id):
        agency = restapi.access.get_agency(request.user, agency_id)
        serializer = serializers.RuleSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        rule = self._wrap_validation_exceptions(automation.rules.Rule.objects.create, request, agency, **data)
        serializer = serializers.RuleSerializer(rule)
        return self.response_ok(serializer.data, status=201)

    def list(self, request, agency_id, credit_id=None):
        agency = restapi.access.get_agency(request.user, agency_id)
        rules = automation.rules.Rule.objects.filter(agency=agency).exclude_archived().order_by("id")
        paginator = StandardPagination()
        rules_paginated = paginator.paginate_queryset(rules, request)
        return paginator.get_paginated_response(
            serializers.RuleSerializer(rules_paginated, many=True, context={"request": request}).data
        )

    def put(self, request, agency_id, rule_id):
        agency = restapi.access.get_agency(request.user, agency_id)
        serializer = serializers.RuleSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rule = agency.rule_set.get(id=rule_id)
        self._wrap_validation_exceptions(rule.update, request, **data)
        return self.response_ok(serializers.RuleSerializer(rule, context={"request": request}).data)

    def _wrap_validation_exceptions(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except utils.exc.MultipleValidationError as err:
            errors = {}
            for e in err.errors:
                if isinstance(e, automation.rules.InvalidTargetType):
                    errors.setdefault("target_type", []).append(str(e))
                if isinstance(e, automation.rules.InvalidActionType):
                    errors.setdefault("action_type", []).append(str(e))
                if isinstance(e, automation.rules.InvalidCooldown):
                    errors.setdefault("action_frequency", []).append(str(e))
                if isinstance(e, automation.rules.InvalidWindow):
                    errors.setdefault("window", []).append(str(e))
                if isinstance(e, automation.rules.InvalidChangeLimit):
                    errors.setdefault("change_limit", []).append(str(e))
                if isinstance(e, automation.rules.InvalidChangeStep):
                    errors.setdefault("change_step", []).append(str(e))
                if isinstance(e, automation.rules.InvalidSendEmailSubject):
                    errors.setdefault("send_email_subject", []).append(str(e))
                if isinstance(e, automation.rules.InvalidSendEmailBody):
                    errors.setdefault("send_email_body", []).append(str(e))
                if isinstance(e, automation.rules.InvalidSendEmailRecipients):
                    errors.setdefault("send_email_recipients", []).append(str(e))
                if isinstance(e, automation.rules.InvalidPublisherGroup):
                    errors.setdefault("publisher_group_id", []).append(str(e))
                if isinstance(e, automation.rules.InvalidNotificationRecipients):
                    errors.setdefault("notification_recipients", []).append(str(e))
                if isinstance(e, automation.rules.InvalidRuleConditions):
                    if e.conditions_errors:
                        errors["conditions"] = e.conditions_errors
                    else:
                        errors.setdefault("conditions", []).append(str(e))
            raise utils.exc.ValidationError(errors=errors)
