import datetime

from django import test

import analytics.client_report


class ManagementReportTestCase(test.TestCase):
    fixtures = ["test_projections"]

    def test_client_report_html(self):
        report = analytics.client_report.get_weekly_report_html()
        self.assertIn("<table", report)
        self.assertIn("</table>", report)

    def test_rows(self):
        rows = analytics.client_report._prepare_table_rows(datetime.date(2017, 2, 14))
        self.assertEqual(
            rows[0].as_html(1),
            "<tr><td>February 14</td><td># blacklisted publishers</td>"
            "<td># self-managed actions</td><td># different users seen</td></tr>",
        )
        self.assertEqual(
            rows[-1].as_html(2), "<tr><td><b></b></td><td><b>0</b></td><td><b>0</b></td><td><b>0</b></td></tr>"
        )
