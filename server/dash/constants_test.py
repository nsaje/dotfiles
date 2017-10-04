import decimal

from django.test import TestCase

from dash import constants


class TestConstant(constants.ConstantBase):
    CONS1 = 'cons1'
    CONS2 = 'cons2'
    CONS3 = 'cons3'

    _VALUES = {
        CONS1: 'Cons1',
        CONS2: 'Cons2',
        CONS3: 'Cons3'
    }

    @classmethod
    def test_func(cls):
        return


class TestConstantNoValues(constants.ConstantBase):
    CONS1 = 'cons1'
    CONS2 = 'cons2'
    CONS3 = 'cons3'

    @classmethod
    def test_func(cls):
        return


class ConstantsBaseTestCase(TestCase):
    def test_get_all(self):
        constants = TestConstant.get_all()
        self.assertEqual(len(constants), 3)
        self.assertTrue('cons1' in constants)
        self.assertTrue('cons2' in constants)
        self.assertTrue('cons3' in constants)

    def test_get_choices(self):
        choices = tuple(TestConstant.get_choices())
        self.assertEqual(len(choices), 3)
        self.assertTrue(('cons1', 'Cons1') in choices)
        self.assertTrue(('cons2', 'Cons2') in choices)
        self.assertTrue(('cons3', 'Cons3') in choices)

    def test_get_text(self):
        self.assertEqual(TestConstant.get_text('cons2'), 'Cons2')
        self.assertIs(TestConstant.get_text('cons100'), None)
        self.assertRaises(AttributeError, TestConstantNoValues.get_text, 'cons1')


class SourceAllRTBRTBTestCase(TestCase):

    def setUp(self):
        self.bcm_modifiers = {
            'fee': decimal.Decimal('0.15'),
            'margin': decimal.Decimal('0.33'),
        }

    def test_get_etfm_min_cpc(self):
        self.assertEqual(
            decimal.Decimal('0.01'),
            constants.SourceAllRTB.get_etfm_min_cpc()
        )

    def test_get_etfm_min_cpc_with_bcm_modifiers(self):
        self.assertEqual(
            decimal.Decimal('0.018'),
            constants.SourceAllRTB.get_etfm_min_cpc(self.bcm_modifiers)
        )

    def test_get_etfm_max_cpc(self):
        self.assertEqual(
            decimal.Decimal('7.0'),
            constants.SourceAllRTB.get_etfm_max_cpc()
        )

    def test_get_etfm_max_cpc_with_bcm_modifiers(self):
        self.assertEqual(
            decimal.Decimal('12.291'),
            constants.SourceAllRTB.get_etfm_max_cpc(self.bcm_modifiers)
        )

    def test_get_etfm_min_daily_budget(self):
        self.assertEqual(
            decimal.Decimal('1'),
            constants.SourceAllRTB.get_etfm_min_daily_budget()
        )

    def test_get_etfm_min_daily_budget_with_bcm_modifiers(self):
        self.assertEqual(
            decimal.Decimal('2'),
            constants.SourceAllRTB.get_etfm_min_daily_budget(self.bcm_modifiers)
        )

    def test_get_etfm_max_daily_budget(self):
        self.assertEqual(
            decimal.Decimal('10000.0'),
            constants.SourceAllRTB.get_etfm_max_daily_budget()
        )

    def test_get_etfm_max_daily_budget_with_bcm_modifiers(self):
        self.assertEqual(
            decimal.Decimal('17559'),
            constants.SourceAllRTB.get_etfm_max_daily_budget(self.bcm_modifiers)
        )
