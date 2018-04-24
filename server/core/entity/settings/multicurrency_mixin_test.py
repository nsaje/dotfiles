from decimal import Decimal
from mock import patch

import django.db.models
from django.test import TestCase

import core.multicurrency
from dash import constants
import utils.dates_helper
from .multicurrency_mixin import MulticurrencySettingsMixin
from .update_object import UpdateObject


class TestSettings(MulticurrencySettingsMixin, django.db.models.Model):
    class Meta:
        app_label = 'dash'
        abstract = True

    a = django.db.models.DecimalField(max_digits=10, decimal_places=2)
    b = django.db.models.DecimalField(max_digits=10, decimal_places=6)
    c = django.db.models.DecimalField(max_digits=10, decimal_places=4)
    local_a = django.db.models.DecimalField(max_digits=10, decimal_places=2)
    local_b = django.db.models.DecimalField(max_digits=10, decimal_places=6)

    multicurrency_fields = ['a', 'b']

    def get_currency(self):
        return constants.Currency.EUR

    def copy_settings(self):
        return UpdateObject(self)


class MulticurrencySettingsMixinTest(TestCase):

    @patch.object(core.multicurrency, 'get_exchange_rate')
    def test_get_counterpart_usd(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = Decimal('2.0')
        today = utils.dates_helper.local_today()

        settings = TestSettings()
        new_settings = settings.copy_settings()

        new_settings.a = Decimal('1.0')
        self.assertEqual(new_settings.local_a, Decimal('2.0'))

        mock_get_exchange_rate.assert_called_with(today, constants.Currency.EUR)

    @patch.object(core.multicurrency, 'get_exchange_rate')
    def test_get_counterpart_local(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = Decimal('2.0')
        today = utils.dates_helper.local_today()

        settings = TestSettings()
        new_settings = settings.copy_settings()

        new_settings.local_b = Decimal('1.0')
        self.assertEqual(new_settings.b, Decimal('0.5'))

        mock_get_exchange_rate.assert_called_with(today, constants.Currency.EUR)

    @patch.object(core.multicurrency, 'get_exchange_rate')
    def test_get_counterpart_none(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = Decimal('2.0')

        settings = TestSettings()
        new_settings = settings.copy_settings()

        new_settings.c = Decimal('1.0')
        self.assertEqual(new_settings.c, Decimal('1.0'))

        mock_get_exchange_rate.assert_not_called()
