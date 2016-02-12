import unittest

from decimal import Decimal
from utils import lc_helper


class LcHelperTestCase(unittest.TestCase):

    def test_basics(self):
        d = Decimal('-1234567.8901')
        self.assertEqual(lc_helper.format_currency(d, curr='$'), '-$1,234,567.89')
        self.assertEqual(lc_helper.default_currency(d), '-$1,234,567.89')

        self.assertEqual(lc_helper.format_currency(d, places=0, sep='.', dp='', neg='', trailneg='-'), '1.234.568-')
        self.assertEqual(lc_helper.format_currency(d, curr='$', neg='(', trailneg=')'), '($1,234,567.89)')
        self.assertEqual(lc_helper.format_currency(d, sep=' '), '-1 234 567.89')
