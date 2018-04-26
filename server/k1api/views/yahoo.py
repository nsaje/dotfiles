import logging

from django.db.models import F

import core.entity
import core.features.yahoo_accounts

from . import base

logger = logging.getLogger(__name__)


class YahooAccountsView(base.K1APIView):

    def get(self, request):

        account_ids = request.GET.get('account_ids')
        if account_ids:
            account_ids = account_ids.split(',')

        accounts = core.entity.Account.objects.filter(yahoo_account__isnull=False)

        if account_ids:
            accounts = accounts.filter(id__in=account_ids)

        return self.response_ok(
            list(
                accounts.annotate(
                    account_id=F('id'),
                    advertiser_id=F('yahoo_account__advertiser_id')
                ).values('account_id', 'advertiser_id')
            )
        )
