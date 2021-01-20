from django.test import TestCase

from . import csv_utils


class DictListToCsvTest(TestCase):
    def test_dictlist_to_csv(self):
        fields = ["Field 1", "Field 3", "Field 2"]
        rows = [{"Field 1": "Value 1", "Field 2": "Value 2"}]

        expected = '"Field 1","Field 3","Field 2"\r\n' '"Value 1","","Value 2"\r\n'

        self.assertEqual(expected, csv_utils.dictlist_to_csv(fields, rows))

    def test_prepend_formula_output(self):
        fields = ["Field 1", "Field 2", "Field 3", "Field 4"]
        rows = [{"Field 1": "=Value 1", "Field 2": "+Value 2", "Field 3": "-Value 3", "Field 4": "@Value 4"}]

        expected = (
            '"Field 1","Field 2","Field 3","Field 4"\r\n' '"\'=Value 1","\'+Value 2","\'-Value 3","\'@Value 4"\r\n'
        )

        self.assertEqual(expected, csv_utils.dictlist_to_csv(fields, rows))
