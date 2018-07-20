from decimal import Decimal
from django.test import TestCase

from . import calculations


class Calculations(TestCase):
    def test_apply_fee(self):
        fee = Decimal("0.15")
        spend = 100

        x = calculations.apply_fee(spend, fee)

        self.assertAlmostEqual(x, Decimal("117.6470"), delta=Decimal("0.0001"))

    def test_apply_margin(self):
        margin = Decimal("0.15")
        spend = 100

        x = calculations.apply_fee(spend, margin)

        self.assertAlmostEqual(x, Decimal("117.6470"), delta=Decimal("0.0001"))

    def test_apply_fee_and_margin(self):
        margin = Decimal("0.11")
        fee = Decimal("0.15")
        spend = 100

        x = calculations.apply_fee_and_margin(spend, fee, margin)

        self.assertAlmostEqual(x, Decimal("132.1877"), delta=Decimal("0.0001"))

    def test_calculate_fee(self):
        fee = Decimal("0.15")
        spend = 100

        x = calculations.calculate_fee(spend, fee)

        self.assertAlmostEqual(x, Decimal("17.6470"), delta=Decimal("0.0001"))

    def test_calculate_margin(self):
        margin = Decimal("0.15")
        spend = 100

        x = calculations.calculate_fee(spend, margin)

        self.assertAlmostEqual(x, Decimal("17.6470"), delta=Decimal("0.0001"))

    def test_calculate_fee_and_margin(self):
        margin = Decimal("0.11")
        fee = Decimal("0.15")
        spend = 100

        x = calculations.calculate_fee_and_margin(spend, fee, margin)

        self.assertAlmostEqual(x, Decimal("32.1877"), delta=Decimal("0.0001"))

    def test_subtract_fee_and_margin(self):
        margin = Decimal("0.1")
        fee = Decimal("0.2")
        spend = 100

        x = calculations.subtract_fee_and_margin(spend, fee, margin)

        self.assertEqual(x, Decimal("72"))
