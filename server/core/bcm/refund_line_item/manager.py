import core.common
import calendar

from django.db import transaction

from . import model


class RefundLineItemManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, **kwargs):
        start_date = kwargs.get("start_date")
        end_date = start_date.replace(day=calendar.monthrange(start_date.year, start_date.month)[1])
        refund = model.RefundLineItem(created_by=request.user if request else None, end_date=end_date, **kwargs)
        refund.clean_save(request)
        return refund
