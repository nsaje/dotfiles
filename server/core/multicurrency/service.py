from .currency_exchange_rate import CurrencyExchangeRate


def get_exchange_rate(date, currency):
    exchange_rate = CurrencyExchangeRate.objects.filter(
        date__lte=date, currency=currency
    ).latest('date')
    return exchange_rate.exchange_rate
