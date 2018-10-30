import core.features.multicurrency
import dash.constants
from utils import db_for_reads

from .base import K1APIView


class CurrencyExchangeRateView(K1APIView):
    @db_for_reads.use_read_replica()
    def get(self, request):
        currencies = request.GET.get("currencies")
        if currencies:
            currencies = currencies.split(",")
        else:
            currencies = dash.constants.Currency.get_all()

        response = {}
        for currency in currencies:
            try:
                response[currency] = core.features.multicurrency.get_current_exchange_rate(currency)
            except core.features.multicurrency.CurrencyExchangeRate.DoesNotExist:
                return self.response_error('Currency exchange rate for currency "{}" does not exist'.format(currency))
        return self.response_ok(response)
