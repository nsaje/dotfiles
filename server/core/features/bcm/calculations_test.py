from decimal import Decimal

from django.test import TestCase

from . import calculations


class Calculations(TestCase):
    def test_apply_fee(self):
        fee = Decimal("0.15")
        spend = 100

        x = calculations.apply_fee(spend, fee)

        self.assertAlmostEqual(x, Decimal("117.6470"), delta=Decimal("0.0001"))

    def test_apply_fees_and_margin(self):
        margin = Decimal("0.11")
        fee = Decimal("0.15")
        service_fee = Decimal("0.10")
        spend = 100

        x = calculations.apply_fees_and_margin(spend, service_fee, fee, margin)

        self.assertAlmostEqual(x, Decimal("146.8752"), delta=Decimal("0.0001"))

    def test_calculate_fee(self):
        fee = Decimal("0.15")
        spend = 100

        x = calculations.calculate_fee(spend, fee)

        self.assertAlmostEqual(x, Decimal("17.6470"), delta=Decimal("0.0001"))

    def test_calculate_fees_and_margin(self):
        margin = Decimal("0.11")
        fee = Decimal("0.15")
        service_fee = Decimal("0.10")
        spend = 100

        x = calculations.calculate_fees_and_margin(spend, service_fee, fee, margin)

        self.assertAlmostEqual(x, Decimal("46.8752"), delta=Decimal("0.0001"))

    def test_subtract_fees_and_margin(self):
        margin = Decimal("0.1")
        fee = Decimal("0.2")
        service_fee = Decimal("0.1")
        spend = 100

        x = calculations.subtract_fees_and_margin(spend, service_fee, fee, margin)

        self.assertEqual(x, Decimal("64.8"))
