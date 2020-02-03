import decimal

from django.test import TestCase

from . import decimal_helpers


class TestMultiplyAsDecimals(TestCase):
    def test_multiply_floats(self):
        result = decimal_helpers.multiply_as_decimals(3.141592653589793, 2.5)
        self.assertEqual(result, decimal.Decimal("7.8540"))

    def test_multiply_floats_increase_precision(self):
        result = decimal_helpers.multiply_as_decimals(3.141592653589793, 2.5, precision=decimal.Decimal("1.000000"))
        self.assertEqual(result, decimal.Decimal("7.853982"))

    def test_multiply_float_and_decimal(self):
        result = decimal_helpers.multiply_as_decimals(3.141592653589793, decimal.Decimal(2.5))
        self.assertEqual(result, decimal.Decimal("7.8540"))

    def test_multiply_decimals(self):
        result = decimal_helpers.multiply_as_decimals(decimal.Decimal(3.141592653589793), decimal.Decimal(2.5))
        self.assertEqual(result, decimal.Decimal("7.8540"))

    def test_multiply_strings(self):
        result = decimal_helpers.multiply_as_decimals("3.141592653589793", "2.5")
        self.assertEqual(result, decimal.Decimal("7.8540"))


class TestEqualDecimals(TestCase):
    def test_default_precision(self):
        self.assertTrue(decimal_helpers.equal_decimals(decimal.Decimal("3.141592653589793"), decimal.Decimal("3.1416")))

    def test_increase_precision(self):
        self.assertFalse(
            decimal_helpers.equal_decimals(
                decimal.Decimal("3.141592653589793"), decimal.Decimal("3.1416"), precision=decimal.Decimal("1.000000")
            )
        )
