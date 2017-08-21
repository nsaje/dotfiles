from decimal import Decimal
from django.test import TestCase

import calculations


class Calculations(TestCase):

    def test_apply_fee(self):
        fee = Decimal('0.15')
        spend = 100

        x = calculations.apply_fee(spend, fee)

        self.assertAlmostEqual(x, Decimal('117.6470'), delta=Decimal('0.0001'))

    def test_apply_margin(self):
        margin = Decimal('0.15')
        spend = 100

        x = calculations.apply_fee(spend, margin)

        self.assertAlmostEqual(x, Decimal('117.6470'), delta=Decimal('0.0001'))

    def test_apply_fee_and_margin(self):
        margin = Decimal('0.11')
        fee = Decimal('0.15')
        spend = 100

        x = calculations.apply_fee_and_margin(spend, fee, margin)

        self.assertAlmostEqual(x, Decimal('132.1877'), delta=Decimal('0.0001'))
