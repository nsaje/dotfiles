
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
