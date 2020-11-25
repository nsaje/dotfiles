import decimal

import django.db.models

import core.features.multicurrency

MULTICURRENCY_FIELD_PREFIX = "local_"


class MulticurrencySettingsMixin(object):
    def get_multicurrency_counterpart(self, field, value):
        to_usd_field = None
        to_local_field = None

        if field.startswith(MULTICURRENCY_FIELD_PREFIX):
            to_usd_field = field[len(MULTICURRENCY_FIELD_PREFIX) :]
        else:
            to_local_field = MULTICURRENCY_FIELD_PREFIX + field

        if field not in self.multicurrency_fields and to_usd_field not in self.multicurrency_fields:
            return None, None

        if not value:
            return to_usd_field or to_local_field, value

        value = decimal.Decimal(value)

        if to_local_field:
            new_local = self._round(to_local_field, value * self._get_exchange_rate())
            if self._is_rounding_error(to_local_field, new_local):
                return None, None
            return to_local_field, new_local
        else:
            new_usd = self._round(to_usd_field, value / self._get_exchange_rate())
            if self._is_rounding_error(to_usd_field, new_usd):
                return None, None
            return to_usd_field, new_usd

    def _get_exchange_rate(self):
        currency = self.get_currency()
        return core.features.multicurrency.get_current_exchange_rate(currency)

    def _round(self, field_name, number):
        field = self._meta.get_field(field_name)
        assert isinstance(field, django.db.models.DecimalField)
        return number.quantize(decimal.Decimal("10") ** -field.decimal_places)

    def _is_rounding_error(self, field_name, value):
        return False
