from django.db import transaction

import core.common

from . import model


class DirectDealConnectionManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, deal, account=None, campaign=None, adgroup=None):
        deal_connection = self._prepare(deal, account=account, campaign=campaign, adgroup=adgroup)
        deal_connection.save(request)
        return deal_connection

    @staticmethod
    def _prepare(deal, account=None, campaign=None, adgroup=None):
        deal_connection = model.DirectDealConnection(deal=deal, account=account, campaign=campaign, adgroup=adgroup)
        return deal_connection

    def clone(self, request, source_deal_connection, account=None, campaign=None, adgroup=None):
        return self.create(request, source_deal_connection.deal, account, campaign, adgroup)
