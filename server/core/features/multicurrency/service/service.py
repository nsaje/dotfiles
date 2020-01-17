import datetime
from decimal import Decimal
from typing import Optional
from typing import Union

import dash.constants
import utils.dates_helper
import utils.lc_helper

from ..constants import CurrencySymbol
from ..currency_exchange_rate import CurrencyExchangeRate


def get_current_exchange_rate(currency: str):
    return get_exchange_rate(utils.dates_helper.local_today(), currency)


def get_exchange_rate(date: datetime.date, currency: str):
    if currency == dash.constants.Currency.USD:
        return Decimal("1.0000")
    exchange_rate = CurrencyExchangeRate.objects.filter(date__lte=date, currency=currency).latest("date")
    return exchange_rate.exchange_rate


def get_currency_symbol(currency: str) -> Optional[str]:
    return CurrencySymbol.get(currency)


def format_value_in_currency(value: Union[int, float], places: int, rounding: str, currency: str) -> str:
    return utils.lc_helper.format_currency(
        Decimal(value) * get_current_exchange_rate(currency),
        places=places,
        rounding=rounding,
        curr=get_currency_symbol(currency),
    )
