import json

from django.core.urlresolvers import reverse

import core.multicurrency
import dash.constants

from .base_test import K1APIBaseTest

from utils import dates_helper
from utils.magic_mixer import magic_mixer


class CurrencyExchangeRateViewTest(K1APIBaseTest):

    def setUp(self):
        magic_mixer.blend(
            core.multicurrency.CurrencyExchangeRate,
            date=dates_helper.local_today(),
            currency=dash.constants.Currency.EUR,
            exchange_rate='0.987',
        )
        super().setUp()

    def test_get(self):
        response = self.client.get(reverse('k1api.currency_exchange_rates'))
        data = json.loads(response.content)
        self.assertEqual({'response': {'USD': '1.0000', 'EUR': '0.9870'}, 'error': None}, data)

    def test_get_specific(self):
        response = self.client.get(reverse('k1api.currency_exchange_rates'), {'currencies': ['EUR']})
        data = json.loads(response.content)
        self.assertEqual({'response': {'EUR': '0.9870'}, 'error': None}, data)

    def test_get_non_existent(self):
        response = self.client.get(reverse('k1api.currency_exchange_rates'), {'currencies': ['FOO']})
        data = json.loads(response.content)
        self.assertEqual(
            {'error': 'Currency exchange rate for currency "FOO" does not exist', 'response': None},
            data
        )
