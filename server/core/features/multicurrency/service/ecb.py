import decimal
from typing import Dict

import requests
from defusedxml import ElementTree

import dash.constants

ECB_EXCHANGE_RATES_XML = "http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


class NotSupportedByECBException(Exception):
    pass


def try_get_exchange_rate(currency: str) -> decimal.Decimal:
    ecb_exchange_rates = _fetch_ecb_exchange_rates()
    eur_exchange_rate = _try_get_eur_exchange_rate(ecb_exchange_rates, currency)
    return 1 / ecb_exchange_rates[dash.constants.Currency.USD] * eur_exchange_rate


def _try_get_eur_exchange_rate(ecb_exchange_rates: Dict[str, decimal.Decimal], currency: str) -> decimal.Decimal:
    if currency == dash.constants.Currency.EUR:
        return decimal.Decimal(1)
    if currency not in ecb_exchange_rates:
        raise NotSupportedByECBException("Currency not supported by ECB")
    return ecb_exchange_rates[currency]


def _fetch_ecb_exchange_rates() -> Dict[str, decimal.Decimal]:
    r = requests.get(ECB_EXCHANGE_RATES_XML)
    root = ElementTree.fromstring(r.content)

    namespaces = {"xmlns": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}
    iterator = root.iterfind("./xmlns:Cube/xmlns:Cube/xmlns:Cube", namespaces=namespaces)

    currency_map = {element.attrib["currency"]: decimal.Decimal(element.attrib["rate"]) for element in iterator}
    return currency_map
