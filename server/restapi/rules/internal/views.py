import rest_framework.permissions
import rest_framework.serializers

import automation.rules
import restapi.access
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
        serializer = serializers.RuleSerializer(rule)
        return self.response_ok(data=serializer.data)

    def create(self, request, agency_id):
        agency = restapi.access.get_agency(request.user, agency_id)
        serializer = serializers.RuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        rule = automation.rules.Rule.objects.create(request, agency, **data)
        serializer = serializers.RuleSerializer(rule)
        return self.response_ok(serializer.data, status=201)

    def list(self, request, agency_id, credit_id=None):
        agency = restapi.access.get_agency(request.user, agency_id)
        rules = automation.rules.Rule.objects.filter(agency=agency).order_by("id")
        paginator = StandardPagination()
        rules_paginated = paginator.paginate_queryset(rules, request)
        return paginator.get_paginated_response(serializers.RuleSerializer(rules_paginated, many=True).data)

    def put(self, request, agency_id, rule_id):
        agency = restapi.access.get_agency(request.user, agency_id)
        serializer = serializers.RuleSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rule = agency.rule_set.get(id=rule_id)
        rule.update(request, **data)
        return self.response_ok(serializers.RuleSerializer(rule).data)
