import core.features.yahoo_accounts
import core.models
import structlog

from . import base

logger = structlog.get_logger(__name__)


class YahooAccountsView(base.K1APIView):
    def get(self, request):

        account_ids = request.GET.get("account_ids")
        if account_ids:
            account_ids = account_ids.split(",")

        accounts = core.models.Account.objects.filter(yahoo_account__isnull=False).select_related("yahoo_account")

        if account_ids:
            accounts = accounts.filter(id__in=account_ids)

        response = []
        for account in accounts:
            response.append(
                {
                    "account_id": account.id,
                    "advertiser_id": account.yahoo_account.advertiser_id,
                    "currency": account.yahoo_account.currency,
                }
            )

        return self.response_ok(response)
