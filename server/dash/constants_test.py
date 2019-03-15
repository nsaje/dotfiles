
from django.test import TestCase

from dash import constants


class TestConstant(constants.ConstantBase):
    CONS1 = "cons1"
    CONS2 = "cons2"
    CONS3 = "cons3"

    _VALUES = {CONS1: "Cons1", CONS2: "Cons2", CONS3: "Cons3"}

    @classmethod
    def test_func(cls):
        return


class TestConstantNoValues(constants.ConstantBase):
    CONS1 = "cons1"
    CONS2 = "cons2"
    CONS3 = "cons3"

    @classmethod
    def test_func(cls):
        return


class ConstantsBaseTestCase(TestCase):
    def test_get_all(self):
        constants = TestConstant.get_all()
        self.assertEqual(len(constants), 3)
        self.assertTrue("cons1" in constants)
        self.assertTrue("cons2" in constants)
        self.assertTrue("cons3" in constants)

    def test_get_all_names(self):
        constants = TestConstant.get_all_names()
        self.assertEqual(len(constants), 3)
        self.assertTrue("CONS1" in constants)
        self.assertTrue("CONS2" in constants)
        self.assertTrue("CONS3" in constants)

    def test_get_choices(self):
        choices = tuple(TestConstant.get_choices())
        self.assertEqual(len(choices), 3)
        self.assertTrue(("cons1", "Cons1") in choices)
        self.assertTrue(("cons2", "Cons2") in choices)
        self.assertTrue(("cons3", "Cons3") in choices)

    def test_get_name(self):
        self.assertEqual(TestConstant.get_name("cons2"), "CONS2")
        self.assertRaises(KeyError, TestConstant.get_name, "cons100")
        self.assertRaises(KeyError, TestConstantNoValues.get_name, "cons100")

    def test_get_text(self):
        self.assertEqual(TestConstant.get_text("cons2"), "Cons2")
        self.assertIsNone(TestConstant.get_text("cons100"))
        self.assertRaises(AttributeError, TestConstantNoValues.get_text, "cons1")

    def test_get_value(self):
        self.assertEqual(TestConstant.get_value("Cons2"), "cons2")
        self.assertIsNone(TestConstant.get_value("Cons100"))
        self.assertRaises(AttributeError, TestConstantNoValues.get_value, "Cons1")

    def test_get_constant_value(self):
        self.assertEqual(TestConstant.get_constant_value("CONS2"), "cons2")
        self.assertEqual(TestConstantNoValues.get_constant_value("CONS1"), "cons1")
        self.assertIsNone(TestConstant.get_constant_value("CONS100"))
        self.assertIsNone(TestConstantNoValues.get_constant_value("CONS100"))
