import datetime
import decimal

from django.test import TestCase

from etl import helpers


class HelpersTest(TestCase):

    def test_get_local_date_context(self):
        context = helpers.get_local_date_context(datetime.date(2016, 5, 1))

        self.assertDictEqual(context, {
            'date': '2016-05-01',
            'tzdate_from': datetime.date(2016, 5, 1),
            'tzhour_from': 4,
            'tzdate_to': datetime.date(2016, 5, 2),
            'tzhour_to': 4,
        })

    def test_calculate_effective_cost(self):
        factors = (0.2, 0.1)

        effective_cost, effective_data_cost, license_fee = helpers.calculate_effective_cost(250, 300, factors)

        self.assertEqual(effective_cost, 50.0)
        self.assertEqual(effective_data_cost, 60.0)
        self.assertEqual(license_fee, 11.0)
