import logging

import core.entity
import core.features.yahoo_accounts

from . import base

logger = logging.getLogger(__name__)


class YahooAccountsView(base.K1APIView):

    def get(self, request):

        account_ids = request.GET.get('account_ids')
        if account_ids:
            account_ids = account_ids.split(',')

        yahoo_accounts = core.features.yahoo_accounts.YahooAccount.objects.all()

        if account_ids:
            yahoo_accounts = yahoo_accounts.filter(account_id__in=account_ids)

        return self.response_ok(list(yahoo_accounts.values('account_id', 'advertiser_id')))
