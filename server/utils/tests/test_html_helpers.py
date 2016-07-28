from decimal import Decimal

from django.test import TestCase

from utils.html_helpers import TableCell, TableRow


class HtmlHelpersTest(TestCase):

    def test_tablecell(self):
        self.assertEqual(
            TableCell(Decimal('1200000.1')).as_html(),
            '<td>$1,200,000</td>'
        )
        self.assertEqual(
            TableCell('Something').as_html(),
            '<td>Something</td>'
        )
        self.assertEqual(
            TableCell('Something', align='right').as_html(),
            '<td align="right">Something</td>'
        )
        self.assertEqual(
            TableCell(10).as_html(),
            '<td>10</td>'
        )

    def test_tablerow(self):
        self.assertEqual(
            TableRow([
                TableCell(1),
                TableCell(2),
                TableCell(3),
            ]).as_html(),
            '<tr><td>1</td><td>2</td><td>3</td></tr>'
        )
        self.assertEqual(
            TableRow([
                TableCell(1),
                TableCell(2),
                TableCell(3),
            ], row_type='totals').as_html(),
            '<tr><td><b>1</b></td><td><b>2</b></td><td><b>3</b></td></tr>'
        )
