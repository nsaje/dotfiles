import core.common

from . import model


class RefundLineItemManager(core.common.BaseManager):

    def create(self, request, **kwargs):
        refund = model.RefundLineItem(
            created_by=request.user,
            **kwargs,
        )
        refund.save(request)
        return refund
