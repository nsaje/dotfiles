import rest_framework.permissions
import rest_framework.serializers
from django.db.models import Q

import automation.rules
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class CanUseAutomationRulesPermission(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.fea_can_create_automation_rules"))


class RuleViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated, CanUseAutomationRulesPermission)

    def get(self, request, rule_id):
        rule = zemauth.access.get_automation_rule(request.user, Permission.READ, rule_id)
        serializer = serializers.RuleSerializer(rule, context={"request": request})
        return self.response_ok(data=serializer.data)

    def create(self, request):
        serializer = serializers.RuleSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        agency = (
            zemauth.access.get_agency(request.user, Permission.WRITE, data.get("agency_id"))
            if data.get("agency_id")
            else None
        )
        account = (
            zemauth.access.get_account(request.user, Permission.WRITE, data.get("account_id"))
            if data.get("account_id")
            else None
        )

        rule = self._wrap_validation_exceptions(
            automation.rules.Rule.objects.create, request, agency=agency, account=account, **data
        )
        serializer = serializers.RuleSerializer(rule)
        return self.response_ok(serializer.data, status=201)

    def list(self, request):
        qpe = serializers.RuleQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")
        agency_only = qpe.validated_data.get("agency_only")

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            if account.agency:
                rules = automation.rules.Rule.objects.filter(
                    Q(account=account) | Q(agency=account.agency)
                ).select_related("agency")
            else:
                rules = automation.rules.Rule.objects.filter(account=account).select_related("agency")

        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            if agency_only:
                rules = automation.rules.Rule.objects.filter(agency=agency).select_related("account")
            else:
                rules = automation.rules.Rule.objects.filter(
                    Q(agency=agency) | Q(account__agency=agency)
                ).select_related("account")

        else:
            raise utils.exc.ValidationError(
                errors={"non_field_errors": "Either agency id or account id must be provided."}
            )

        keyword = qpe.validated_data.get("keyword")
        if keyword:
            rules = rules.filter(name__icontains=keyword)

        rules = rules.exclude_archived().order_by("-created_dt")

        paginator = StandardPagination()
        rules_paginated = paginator.paginate_queryset(rules, request)
        return paginator.get_paginated_response(
            serializers.RuleSerializer(rules_paginated, many=True, context={"request": request}).data
        )

    def put(self, request, rule_id):
        serializer = serializers.RuleSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rule = zemauth.access.get_automation_rule(request.user, Permission.WRITE, rule_id)
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
                if isinstance(e, automation.rules.InvalidAgency):
                    errors.setdefault("agency_id", []).append(str(e))
                if isinstance(e, automation.rules.InvalidAccount):
                    errors.setdefault("account_id", []).append(str(e))
                if isinstance(e, automation.rules.InvalidIncludedAccounts):
                    errors.setdefault("accounts_included", []).append(str(e))
                if isinstance(e, automation.rules.InvalidIncludedCampaigns):
                    errors.setdefault("campaigns_included", []).append(str(e))
                if isinstance(e, automation.rules.InvalidIncludedAdGroups):
                    errors.setdefault("ad_groups_included", []).append(str(e))
            raise utils.exc.ValidationError(errors=errors)


class RuleHistoryViewSet(RESTAPIBaseViewSet):
    def list(self, request):
        qpe = serializers.RuleHistoryQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            rules_histories = automation.rules.RuleHistory.objects.filter(Q(rule__account=account)).order_by(
                "-created_dt"
            )
        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            rules_histories = automation.rules.RuleHistory.objects.filter(
                Q(rule__agency=agency) | Q(rule__account__agency=agency)
            ).order_by("-created_dt")
        else:
            raise utils.exc.ValidationError("Either agency id or account id must be provided.")

        rule_id = qpe.validated_data.get("rule_id")
        if rule_id is not None:
            rules_histories = rules_histories.filter(Q(rule__id=rule_id))

        ad_group_id = qpe.validated_data.get("ad_group_id")
        if ad_group_id is not None:
            rules_histories = rules_histories.filter(Q(ad_group__id=ad_group_id))

        start_date = qpe.validated_data.get("start_date")
        if start_date is not None:
            rules_histories = rules_histories.filter(Q(created_dt__date__gte=start_date))

        end_date = qpe.validated_data.get("end_date")
        if end_date is not None:
            rules_histories = rules_histories.filter(Q(created_dt__date__lte=end_date))

        rules_histories.select_related("rule", "ad_group")

        paginator = StandardPagination()
        rules_histories_paginated = paginator.paginate_queryset(rules_histories, request)
        return paginator.get_paginated_response(
            serializers.RuleHistorySerializer(rules_histories_paginated, many=True, context={"request": request}).data
        )
