import datetime
from collections import OrderedDict

from django import test
import xlrd

from dash import export


class ExportTestCase(test.TestCase):
    def _assert_row(self, worksheet, row_num, row_cell_list):
        for cell_num, cell_value in enumerate(row_cell_list):
            self.assertEqual(worksheet.cell_value(row_num, cell_num), cell_value)

    def setUp(self):
        self.data = [
            {
                'date': datetime.date(2014, 7, 1),
                'cost': 1000.12,
                'clicks': 103,
                'impressions': 100000,
                'ctr': 1.03,
                'some_random_metric': 12
            },
            {
                'date': datetime.date(2014, 7, 1),
                'cost': 1034.12,
                'clicks': 133,
                'impressions': 100308,
                'ctr': 1.04,
                'some_random_metric': 14
            }
        ]

    def test_get_csv_content(self):
        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('cost', 'Cost'),
            ('clicks', 'Clicks'),
            ('ctr', 'CTR')
        ])

        content = export.get_csv_content(fieldnames, self.data)

        expected_content = 'Date,Cost,Clicks,CTR\r\n2014-07-01,1000.12,103,1.03\r\n2014-07-01,1034.12,133,1.04\r\n'

        self.assertEqual(content, expected_content)

    def test_get_excel_content(self):
        columns = [
            {'key': 'date', 'name': 'Date', 'format': 'date'},
            {'key': 'cost', 'name': 'Cost', 'format': 'currency'},
            {'key': 'clicks', 'name': 'Clicks'},
            {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
        ]

        content = export.get_excel_content([('Test Report', columns, self.data)])

        workbook = xlrd.open_workbook(file_contents=content)
        self.assertIsNotNone(workbook)

        worksheet = workbook.sheet_by_name('Test Report')
        self.assertIsNotNone(worksheet)

        self._assert_row(worksheet, 0, ['Date', 'Cost', 'Clicks', 'CTR'])
        self._assert_row(worksheet, 1, [41821.0, 1000.12, 103, 0.0103])
