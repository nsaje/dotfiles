from django.db import transaction

import core.common
import core.common.entity_limits

from . import model


class DirectDealManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, agency, source, deal_id):
        self._validate_entity_limits(agency)
        deal = self._prepare(agency, source, deal_id)
        deal.save(request)
        return deal

    @staticmethod
    def _prepare(agency, source, deal_id):
        deal = model.DirectDeal(agency=agency, source=source, deal_id=deal_id)
        return deal

    @staticmethod
    def _validate_entity_limits(agency):
        core.common.entity_limits.enforce(model.DirectDeal.objects.filter(agency=agency))
