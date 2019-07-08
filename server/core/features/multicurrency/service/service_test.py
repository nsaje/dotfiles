import datetime
from decimal import Decimal

from django.test import TestCase

import dash.constants
from utils.magic_mixer import magic_mixer

from . import service
from ..currency_exchange_rate import CurrencyExchangeRate


class TestMulticurrencyService(TestCase):
    def test_get_exchange_rate(self):
        magic_mixer.blend(
            CurrencyExchangeRate, date=datetime.date(2018, 1, 1), currency=dash.constants.Currency.USD, exchange_rate=1
        )
        magic_mixer.blend(
            CurrencyExchangeRate,
            date=datetime.date(2018, 1, 1),
            currency=dash.constants.Currency.EUR,
            exchange_rate=1.1,
        )
        magic_mixer.blend(
            CurrencyExchangeRate,
            date=datetime.date(2018, 1, 3),
            currency=dash.constants.Currency.EUR,
            exchange_rate=1.2,
        )

        self.assertEqual(
            service.get_exchange_rate(datetime.date(2018, 1, 1), dash.constants.Currency.USD), Decimal("1.0000")
        )
        self.assertEqual(
            service.get_exchange_rate(datetime.date(2018, 1, 1), dash.constants.Currency.EUR), Decimal("1.1000")
        )
        self.assertEqual(
            service.get_exchange_rate(datetime.date(2018, 1, 2), dash.constants.Currency.EUR), Decimal("1.1000")
        )
        self.assertEqual(
            service.get_exchange_rate(datetime.date(2018, 1, 3), dash.constants.Currency.EUR), Decimal("1.2000")
        )
        self.assertEqual(
            service.get_exchange_rate(datetime.date(2018, 1, 4), dash.constants.Currency.EUR), Decimal("1.2000")
        )
