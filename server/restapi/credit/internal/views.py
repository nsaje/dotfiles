import rest_framework.permissions
import rest_framework.response
from django.db.models import Q
from rest_framework import permissions

import core.features.bcm
import core.features.bcm.bcm_slack
import core.features.multicurrency
import dash.constants
import restapi.campaignbudget.internal.serializers
import restapi.common.views_base
import restapi.credit.v1.views
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from utils import dates_helper
from zemauth.features.entity_permission import Permission

from . import helpers
from . import serializers


class CanUseCreditView(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.account_credit_view"))


class CreditViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated, CanUseCreditView)
    serializer = serializers.CreditSerializer
    serializer_totals = serializers.CreditTotalsSerializer
    serializer_budgets = restapi.campaignbudget.internal.serializers.CampaignBudgetSerializer

    def get(self, request, credit_id):
        credit = zemauth.access.get_credit_line_item(
            request.user, Permission.READ, credit_id, prefetch_related_budgets=True
        )
        return self.response_ok(self.serializer(credit, context={"request": request}).data)

    def list(self, request):
        qpe = serializers.CreditQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")
        active = qpe.validated_data.get("active", None)
        exclude_canceled = qpe.validated_data.get("exclude_canceled", None)

        credits_qs = self._get_credits_qs(request, account_id=account_id, agency_id=agency_id)
        if active is not None:
            date = dates_helper.local_today()
            if active:
                credits_qs = credits_qs.filter(end_date__gte=date)
            else:
                credits_qs = credits_qs.filter(end_date__lt=date)

        if exclude_canceled:
            credits_qs = credits_qs.exclude(status=dash.constants.CreditLineItemStatus.CANCELED)

        paginator = StandardPagination()
        credits_paginated = paginator.paginate_queryset(credits_qs, request)
        return paginator.get_paginated_response(
            self.serializer(credits_paginated, many=True, context={"request": request}).data
        )

    def totals(self, request):
        qpe = serializers.CreditQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")

        credits_qs = self._get_credits_qs(request, account_id=account_id, agency_id=agency_id).exclude(
            status=dash.constants.CreditLineItemStatus.PENDING
        )
        totals = helpers.get_totals_for_credits(credits_qs.all())

        return self.response_ok(self.serializer_totals(totals, many=True, context={"request": request}).data)

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        credit = core.features.bcm.CreditLineItem.objects.create(request, **data)
        return self.response_ok(self.serializer(credit, context={"request": request}).data, status=201)

    def put(self, request, credit_id):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        credit = zemauth.access.get_credit_line_item(request.user, Permission.WRITE, credit_id)
        credit.update(request, **data)
        return self.response_ok(self.serializer(credit, context={"request": request}).data)

    def list_budgets(self, request, credit_id):
        credit = zemauth.access.get_credit_line_item(request.user, Permission.READ, credit_id)
        budgets_qs = (
            core.features.bcm.BudgetLineItem.objects.filter(credit=credit)
            .select_related("credit", "campaign")
            .order_by("-created_dt")
        )
        return self.response_ok(self.serializer_budgets(budgets_qs, many=True, context={"request": request}).data)

    @staticmethod
    def _get_credits_qs(request, account_id=None, agency_id=None):
        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            credits_qs = (
                core.features.bcm.CreditLineItem.objects.filter_by_account(account)
                .prefetch_related("budgets")
                .order_by("-start_date", "-end_date", "-created_dt")
            )
        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            credits_qs = (
                core.features.bcm.CreditLineItem.objects.filter(Q(agency=agency) | Q(account__agency=agency))
                .prefetch_related("budgets")
                .order_by("-start_date", "-end_date", "-created_dt")
            )
        else:
            raise utils.exc.ValidationError(
                errors={"non_field_errors": "Either agency id or account id must be provided."}
            )
        return credits_qs
