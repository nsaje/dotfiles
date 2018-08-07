from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.common.pagination import StandardPagination
import restapi.access

from . import serializers
import core.bcm
import utils.exc
import utils.dates_helper


class AccountCreditViewSet(RESTAPIBaseViewSet):
    def get(self, request, account_id, credit_id):
        account = restapi.access.get_account(request.user, account_id)
        credit = (
            core.bcm.CreditLineItem.objects.filter_by_account(account).prefetch_related("budgets").get(id=credit_id)
        )
        return self.response_ok(serializers.AccountCreditSerializer(credit, context={"request": request}).data)

    def list(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        credit_items = (
            core.bcm.CreditLineItem.objects.filter_by_account(account)
            .filter(end_date__gte=utils.dates_helper.local_today())
            .prefetch_related("budgets")
            .order_by("-start_date", "-end_date", "-created_dt")
        )
        paginator = StandardPagination()
        credit_items_paginated = paginator.paginate_queryset(credit_items, request)
        return paginator.get_paginated_response(
            serializers.AccountCreditSerializer(credit_items_paginated, many=True, context={"request": request}).data
        )
