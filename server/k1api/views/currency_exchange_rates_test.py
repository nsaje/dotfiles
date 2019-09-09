import json

from django.urls import reverse

import core.features.multicurrency
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest


class CurrencyExchangeRateViewTest(K1APIBaseTest):
    def setUp(self):
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.EUR,
            exchange_rate="0.987",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.GBP,
            exchange_rate="0.876",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.AUD,
            exchange_rate="0.765",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.SGD,
            exchange_rate="0.654",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.BRL,
            exchange_rate="0.227",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.MYR,
            exchange_rate="0.212",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.CHF,
            exchange_rate="0.862",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.ZAR,
            exchange_rate="13.326",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.ILS,
            exchange_rate="4.0513",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.INR,
            exchange_rate="78.5770",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.JPY,
            exchange_rate="108.0500",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.CAD,
            exchange_rate="1.3234",
        )
        magic_mixer.blend(
            core.features.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.NZD,
            exchange_rate="1.7208",
        )
        super().setUp()

    def test_get(self):
        response = self.client.get(reverse("k1api.currency_exchange_rates"))
        data = json.loads(response.content)
        self.assertEqual(
            {
                "response": {
                    "USD": "1.0000",
                    "EUR": "0.9870",
                    "GBP": "0.8760",
                    "AUD": "0.7650",
                    "SGD": "0.6540",
                    "BRL": "0.2270",
                    "MYR": "0.2120",
                    "CHF": "0.8620",
                    "ZAR": "13.3260",
                    "ILS": "4.0513",
                    "INR": "78.5770",
                    "JPY": "108.0500",
                    "CAD": "1.3234",
                    "NZD": "1.7208",
                },
                "error": None,
            },
            data,
        )

    def test_get_specific(self):
        response = self.client.get(reverse("k1api.currency_exchange_rates"), {"currencies": ["EUR"]})
        data = json.loads(response.content)
        self.assertEqual({"response": {"EUR": "0.9870"}, "error": None}, data)

    def test_get_non_existent(self):
        response = self.client.get(reverse("k1api.currency_exchange_rates"), {"currencies": ["FOO"]})
        data = json.loads(response.content)
        self.assertEqual({"error": 'Currency exchange rate for currency "FOO" does not exist', "response": None}, data)
