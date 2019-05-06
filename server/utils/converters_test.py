from django.test import TestCase

from . import converters


class ConvertersTest(TestCase):
    def test_x_to_bool_true(self):
        self.assertTrue(converters.x_to_bool({"a": 1}))
        self.assertTrue(converters.x_to_bool((0,)))
        self.assertTrue(converters.x_to_bool(-1))
        self.assertTrue(converters.x_to_bool(-2.3))
        self.assertTrue(converters.x_to_bool([0]))
        self.assertTrue(converters.x_to_bool(-1))
        self.assertTrue(converters.x_to_bool(1))
        self.assertTrue(converters.x_to_bool(2))
        self.assertTrue(converters.x_to_bool("1"))
        self.assertTrue(converters.x_to_bool("TRUE"))
        self.assertTrue(converters.x_to_bool("True"))
        self.assertTrue(converters.x_to_bool("T"))
        self.assertTrue(converters.x_to_bool("t"))

    def test_x_to_bool_false(self):
        self.assertFalse(converters.x_to_bool({}))
        self.assertFalse(converters.x_to_bool(()))
        self.assertFalse(converters.x_to_bool([]))
        self.assertFalse(converters.x_to_bool(0))
        self.assertFalse(converters.x_to_bool(0.0))
        self.assertFalse(converters.x_to_bool("0"))
        self.assertFalse(converters.x_to_bool("FALSE"))
        self.assertFalse(converters.x_to_bool("False"))
        self.assertFalse(converters.x_to_bool("F"))
        self.assertFalse(converters.x_to_bool("f"))
        self.assertFalse(converters.x_to_bool("WhatEveR"))
