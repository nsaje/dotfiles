import core.features.bcm
import utils.dates_helper
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class CreditViewSet(RESTAPIBaseViewSet):
    serializer = serializers.CreditSerializer

    def get(self, request, account_id, credit_id):
        account = zemauth.access.get_account(request.user, Permission.READ, account_id)
        credit = (
            core.features.bcm.CreditLineItem.objects.filter_by_account(account)
            .prefetch_related("budgets")
            .get(id=credit_id)
        )
        return self.response_ok(self.serializer(credit, context={"request": request}).data)

    def list(self, request, account_id):
        account = zemauth.access.get_account(request.user, Permission.READ, account_id)
        credit_items = (
            core.features.bcm.CreditLineItem.objects.filter_by_account(account)
            .filter(end_date__gte=utils.dates_helper.local_today())
            .prefetch_related("budgets")
            .order_by("-start_date", "-end_date", "-created_dt")
        )
        paginator = StandardPagination()
        credit_items_paginated = paginator.paginate_queryset(credit_items, request)
        return paginator.get_paginated_response(
            self.serializer(credit_items_paginated, many=True, context={"request": request}).data
        )
