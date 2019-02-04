import dash.constants

from .ecb import fetch_ecb_exchange_rates


def get_exchange_rate():
    exchange_rates = fetch_ecb_exchange_rates()
    return 1 / exchange_rates[dash.constants.Currency.USD] * exchange_rates[dash.constants.Currency.ZAR]
