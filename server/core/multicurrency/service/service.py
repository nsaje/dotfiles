import decimal

import dash.constants
import utils.dates_helper

from ..constants import CurrencySymbol
from ..currency_exchange_rate import CurrencyExchangeRate


def get_current_exchange_rate(currency):
    return get_exchange_rate(utils.dates_helper.local_today(), currency)


def get_exchange_rate(date, currency):
    if currency == dash.constants.Currency.USD:
        return decimal.Decimal('1.0000')
    exchange_rate = CurrencyExchangeRate.objects.filter(
        date__lte=date, currency=currency
    ).latest('date')
    return exchange_rate.exchange_rate


def get_currency_symbol(currency):
    return CurrencySymbol.get(currency)
