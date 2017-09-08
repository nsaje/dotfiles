import datetime
import unittest

from utils import command_helpers


class CommandHelpersTestCase(unittest.TestCase):

    def test_last_n_days(self):
        today = datetime.datetime.utcnow().date()

        days_1 = [
            today,
        ]
        self.assertEqual(days_1, command_helpers.last_n_days(1))

        days_3 = [
            today,
            today - datetime.timedelta(days=1),
            today - datetime.timedelta(days=2),
        ]
        self.assertEqual(days_3, command_helpers.last_n_days(3))

    def test_parse_date(self):
        options = {
            'date': '2016-01-01'
        }

        ret = command_helpers.parse_date(options)
        self.assertEqual(datetime.date(2016, 1, 1), ret)

    def test_parse_date_custom_field_name(self):
        options = {
            'custom_date': '2016-01-01'
        }
        ret = command_helpers.parse_date(options, field_name='custom_date')
        self.assertEqual(datetime.date(2016, 1, 1), ret)

    def test_parse_date_default_value(self):
        options = {
            'date': None
        }

        ret = command_helpers.parse_date(options)
        self.assertEqual(None, ret)

        default = datetime.date(2016, 1, 1)
        ret = command_helpers.parse_date(options, default=default)

        self.assertEqual(default, ret)
