from django.db import transaction

import core.common
import core.common.entity_limits

from . import model


class DirectDealManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, source, deal_id, name, agency=None, account=None):
        if agency is not None:
            self._validate_entity_limits(agency)
        elif account is not None:
            self._validate_entity_limits(account.agency)
        deal = self._prepare(agency, account, source, deal_id, name)
        deal.save(request)
        return deal

    @staticmethod
    def _prepare(agency, account, source, deal_id, name):
        deal = model.DirectDeal(agency=agency, account=account, source=source, deal_id=deal_id, name=name)
        return deal

    @staticmethod
    def _validate_entity_limits(agency):
        core.common.entity_limits.enforce(model.DirectDeal.objects.filter(agency=agency))
