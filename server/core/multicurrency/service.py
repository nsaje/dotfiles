import decimal

import dash.constants

from .currency_exchange_rate import CurrencyExchangeRate


def get_exchange_rate(date, currency):
    if currency == dash.constants.Currency.USD:
        return decimal.Decimal('1.0000')
    exchange_rate = CurrencyExchangeRate.objects.filter(
        date__lte=date, currency=currency
    ).latest('date')
    return exchange_rate.exchange_rate
