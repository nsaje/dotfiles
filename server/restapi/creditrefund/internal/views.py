from rest_framework import permissions
from rest_framework.response import Response

import core.models
import restapi.access
import utils.exc
from core.features.bcm.refund_line_item import exceptions
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.creditrefund.internal import serializers


class CanManageCreditRefundsPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_manage_credit_refunds"))


class CreditRefundViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, CanManageCreditRefundsPermission)

    def get(self, request, credit_id, refund_id):
        credit = restapi.access.get_credit_line_item(request.user, credit_id)
        refund = restapi.access.get_refund_line_item(request.user, refund_id, credit=credit)
        return self.response_ok(serializers.CreditRefundSerializer(refund, context={"request": request}).data)

    def remove(self, request, credit_id, refund_id):
        credit = restapi.access.get_credit_line_item(request.user, credit_id)
        refund = restapi.access.get_refund_line_item(request.user, refund_id, credit=credit)
        self._update_refund(refund.delete)
        return Response(None, status=204)

    def list(self, request, credit_id=None):
        qpe = serializers.CreditRefundQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")

        if credit_id is not None:
            credit = restapi.access.get_credit_line_item(request.user, credit_id)
            refunds_qs = core.features.bcm.refund_line_item.RefundLineItem.objects.filter_by_credit(credit)
        elif account_id is not None:
            account = restapi.access.get_account(request.user, account_id)
            refunds_qs = core.features.bcm.refund_line_item.RefundLineItem.objects.filter_by_account(account)
        elif agency_id is not None:
            agency = restapi.access.get_agency(request.user, agency_id)
            refunds_qs = core.features.bcm.refund_line_item.RefundLineItem.objects.filter_by_agency(agency)
        else:
            raise utils.exc.ValidationError(
                errors={"non_field_errors": "Either agency id, account id or credit id must be provided."}
            )

        paginator = StandardPagination()
        refunds_paginated = paginator.paginate_queryset(refunds_qs, request)
        return paginator.get_paginated_response(
            serializers.CreditRefundSerializer(refunds_paginated, many=True, context={"request": request}).data
        )

    def create(self, request, credit_id):
        credit = restapi.access.get_credit_line_item(request.user, credit_id)
        serializer = serializers.CreditRefundSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        new_refund = self._update_refund(
            core.features.bcm.RefundLineItem.objects.create, request=request, credit=credit, **serializer.validated_data
        )
        return self.response_ok(
            serializers.CreditRefundSerializer(new_refund, context={"request": request}).data, status=201
        )

    @staticmethod
    def _update_refund(fn, **kwargs):
        try:
            refund = fn(**kwargs)

        except exceptions.AccountInvalid as err:
            raise utils.exc.ValidationError(errors={"account_id": [str(err)]})

        except exceptions.StartDateInvalid as err:
            raise utils.exc.ValidationError(errors={"start_date": [str(err)]})

        except exceptions.RefundAmountExceededTotalSpend as err:
            raise utils.exc.ValidationError(errors={"amount": [str(err)]})

        except exceptions.CreditAvailableAmountNegative as err:
            raise utils.exc.ValidationError(errors={"amount": [str(err)]})

        except exceptions.EffectiveMarginAmountOutOfBounds as err:
            raise utils.exc.ValidationError(errors={"effective_margin": [str(err)]})

        return refund
