import datetime
from decimal import Decimal

from django import test

import reports.management_report

import reports.models


class ManagementReportTestCase(test.TestCase):
    fixtures = ['test_projections']

    def setUp(self):
        self.today = datetime.date(2015, 11, 15)

    def test_daily_empty(self):
        table = reports.management_report.get_daily_report_html(self.today)
        print table
        self.assertIn('<caption>Daily Management Report</caption>', table)
        self.assertIn(
            '<div class="section"><table',
            table
        )
        self.assertIn(
            '<td align="right">Managed</td><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>$0</td>',
            table
        )
