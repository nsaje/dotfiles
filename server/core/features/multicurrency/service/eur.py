import dash.constants

from .ecb import fetch_ecb_exchange_rates


def get_exchange_rate():
    return 1 / fetch_ecb_exchange_rates()[dash.constants.Currency.USD]
