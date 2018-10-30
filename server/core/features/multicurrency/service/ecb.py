import decimal

import requests
from defusedxml import ElementTree

ECB_EXCHANGE_RATES_XML = "http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


def fetch_ecb_exchange_rates():
    r = requests.get(ECB_EXCHANGE_RATES_XML)
    root = ElementTree.fromstring(r.content)

    namespaces = {"xmlns": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}
    iterator = root.iterfind("./xmlns:Cube/xmlns:Cube/xmlns:Cube", namespaces=namespaces)

    currency_map = {element.attrib["currency"]: decimal.Decimal(element.attrib["rate"]) for element in iterator}
    return currency_map
