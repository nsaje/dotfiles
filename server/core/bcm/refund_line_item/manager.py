import core.common
import calendar

from . import model


class RefundLineItemManager(core.common.BaseManager):

    def create(self, request, **kwargs):
        start_date = kwargs.pop('start_date')
        end_date = kwargs.pop(
            'end_date',
            start_date.replace(day=calendar.monthrange(start_date.year, start_date.month)[1]),
        )
        refund = model.RefundLineItem(
            created_by=request.user,
            start_date=start_date,
            end_date=end_date,
            **kwargs,
        )
        refund.save(request)
        return refund
