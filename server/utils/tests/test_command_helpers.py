import datetime
import unittest

from utils import command_helpers


class CommandHelpersTestCase(unittest.TestCase):

    def test_last_n_days(self):
        days_1 = [
            datetime.date.today(),
        ]
        self.assertEqual(days_1, command_helpers.last_n_days(1))

        days_3 = [
            datetime.date.today(),
            datetime.date.today() - datetime.timedelta(days=1),
            datetime.date.today() - datetime.timedelta(days=2),
        ]
        self.assertEqual(days_3, command_helpers.last_n_days(3))
