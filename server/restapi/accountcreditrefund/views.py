from restapi.common.views_base import RESTAPIBaseViewSet

from rest_framework import permissions
from rest_framework.response import Response

import restapi.access
from restapi.common.pagination import StandardPagination

import core.entity
from core.bcm.refund_line_item import exceptions

import utils.exc

from . import serializers


class CanManageCreditRefundsPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm('zemauth.can_manage_credit_refunds'))


class AccountCreditRefundViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, CanManageCreditRefundsPermission,)

    def get(self, request, account_id, credit_id, refund_id):
        refund = self._get_refund_query(request, account_id, credit_id).get(id=refund_id)
        return self.response_ok(serializers.AccountCreditRefundSerializer(refund).data)

    def remove(self, request, account_id, credit_id, refund_id):
        refund = self._get_refund_query(request, account_id, credit_id).get(id=refund_id)
        self.update_refund(refund.delete)
        return Response(None, status=204)

    def list(self, request, account_id, credit_id=None):
        refunds = self._get_refund_query(request, account_id, credit_id)
        paginator = StandardPagination()
        refunds_paginated = paginator.paginate_queryset(refunds, request)
        return paginator.get_paginated_response(
            serializers.AccountCreditRefundSerializer(refunds_paginated, many=True).data
        )

    def create(self, request, account_id, credit_id):
        account, credit = self._get_account_and_credit(request, account_id, credit_id)
        serializer = serializers.AccountCreditRefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_refund = self.update_refund(
            core.bcm.RefundLineItem.objects.create,
            request=request,
            account=account,
            credit=credit.get(),
            **serializer.validated_data,
        )
        return self.response_ok(
            serializers.AccountCreditRefundSerializer(new_refund).data,
            status=201,
        )

    @staticmethod
    def _get_account_and_credit(request, account_id, credit_id):
        account = restapi.access.get_account(request.user, account_id)
        credit = core.bcm.CreditLineItem.objects.filter_by_account(account)\
                                                .prefetch_related('budgets')
        if credit_id:
            credit = credit.filter(id=credit_id)

        return account, credit

    @staticmethod
    def _get_refund_query(request, account_id, credit_id=None):
        account, credit = AccountCreditRefundViewSet._get_account_and_credit(
            request, account_id, credit_id,
        )
        return core.bcm.RefundLineItem.objects.filter(
            credit__in=credit,
        )

    def update_refund(self, fn, **kwargs):
        try:
            refund = fn(**kwargs)

        except exceptions.StartDateInvalid as err:
            raise utils.exc.ValidationError(errors={'start_date': [str(err)]})

        except exceptions.RefundAmountExceededTotalSpend as err:
            raise utils.exc.ValidationError(errors={'amount': [str(err)]})

        except exceptions.CreditAvailableAmountNegative as err:
            raise utils.exc.ValidationError(errors={'amount': [str(err)]})

        return refund
