import decimal

import utils.dates_helper
import utils.numbers
import core.multicurrency


MULTICURRENCY_FIELD_PREFIX = 'local_'


class MulticurrencySettingsMixin(object):

    def get_multicurrency_counterpart(self, field, value):
        to_usd_field = None
        to_local_field = None

        if field.startswith(MULTICURRENCY_FIELD_PREFIX):
            to_usd_field = field[len(MULTICURRENCY_FIELD_PREFIX):]
        else:
            to_local_field = MULTICURRENCY_FIELD_PREFIX + field

        if not value or not (field in self.multicurrency_fields or to_usd_field in self.multicurrency_fields):
            return None, None

        value = decimal.Decimal(value)

        if to_local_field:
            new_local = self._round(value * self._get_exchange_rate())
            return to_local_field, new_local
        else:
            new_usd = self._round(value / self._get_exchange_rate())
            return to_usd_field, new_usd

    def _get_exchange_rate(self):
        today = utils.dates_helper.local_today()
        currency = self.get_currency()
        return core.multicurrency.get_exchange_rate(today, currency)

    def _round(self, number):
        return number.quantize(decimal.Decimal('10') ** -4)
