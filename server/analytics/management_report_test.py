import datetime

from django import test

import analytics.management_report
import dash.models
import zemauth.models
from utils.html_helpers import TableCell, TableRow


class FakeContext(object):
    pass


class ManagementReportTestCase(test.TestCase):
    fixtures = ['test_projections']

    def setUp(self):
        self.today = datetime.date(2015, 11, 15)
        self.context = FakeContext()

        self.context.accounts = {
            'this_day': set([3, 4, 5]),
            'prev_day': set([4, 5]),

            'this_week': set([1, 3, 4, 5, 6]),
            'prev_week': set([1, 3, 6, 7, 8]),

            'this_month': set([1, 2, 3, 4, 5, 6]),
            'prev_month': set([1, 3, 5]),
        }
        self.context.agencies = {
            'this_day': set([1]),
            'prev_day': set([1]),

            'this_week': set([1]),
            'prev_week': set(),

            'this_month': set([1]),
            'prev_month': set(),
        }
        self.context.campaigns = {
            'this_day': set([1, 3, 4, 5]),
            'prev_day': set([4, 5]),

            'this_week': set([1, 3, 4, 5, 6]),
            'prev_week': set([1, 3, 6, 7, 8]),

            'this_month': set([1, 2, 3, 4, 5, 6]),
            'prev_month': set([1, 3, 5]),
        }
        self.context.agency_accounts = set([2, 3])
        self.context.agency_campaigns = set([4, 5])

        self.context.account_types = {
            1: 1,
            2: 1,
            3: 2,
            4: 3,
            5: 3,
            6: 4,

        }
        self.context.campaign_types = {
            1: 2,
            2: 2,
            3: 3,
            4: 4,
            5: 5,
        }

    def test_daily_empty(self):
        html = analytics.management_report.get_daily_report_html(self.today)
        self.assertIn('<caption>Daily Management Report</caption>', html)
        self.assertIn(
            '<div class="section"><table',
            html
        )
        self.assertIn(
            '<td align="right">Managed</td><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>$0</td>',
            html
        )

    def test_daily_bcm_lists(self):
        today = datetime.date.today()
        credit = dash.models.CreditLineItem.objects.create_unsafe(
            account_id=1,
            amount=5000,
            start_date=today,
            end_date=today + datetime.timedelta(10),
            status=1,
        )
        dash.models.BudgetLineItem.objects.create_unsafe(
            campaign_id=1,
            credit=credit,
            amount=5000,
            start_date=credit.start_date,
            end_date=credit.end_date
        )

        html = analytics.management_report.get_daily_report_html(
            today
        )
        self.assertIn('<li><a href="https://one.zemanta.com/v2/analytics/account/1">1 - test account 1 - $5000 - ', html)
        self.assertIn('<li><a href="https://one.zemanta.com/v2/analytics/campaign/1">$5000', html)

        html = analytics.management_report.get_daily_report_html(
            today + datetime.timedelta(1)
        )
        self.assertNotIn('<li><a href="https://one.zemanta.com/v2/anlaytics/account/1">1 - test account 1 - $5000', html)
        self.assertNotIn('<li><a href="https://one.zemanta.com/v2/anlaytics/account/1">$5000', html)

    def test_daily_account_campaign_lists(self):
        class Request(object):
            pass
        r = Request()
        r.user = zemauth.models.User.objects.get(pk=1)

        today = datetime.date.today()
        acc = dash.models.Account(
            name='Account 2'
        )
        acc.save(r)
        dash.models.Campaign(
            account=acc,
            name='Campaign 2'
        ).save(r)
        html = analytics.management_report.get_daily_report_html(
            today
        )

        self.assertIn(
            '<li><a href="https://one.zemanta.com/v2/analytics/campaign/3">Account Account 2, Campaign Campaign 2</a></li>', html)
        self.assertIn('<li><a href="https://one.zemanta.com/v2/analytics/account/2">Account Account 2</a></li>', html)

    def test_fixture_context(self):
        context = analytics.management_report.ReportContext(self.today)
        self.assertEqual(context.account_types, {1: 1})
        self.assertEqual(context.campaign_types, {1: 1, 2: 1})
        self.assertEqual(context.agency_accounts, set([]))
        self.assertEqual(context.agency_campaigns, set([]))

    def test_get_totals(self):
        table = [
            [TableCell(10), TableCell(20)],
            [TableCell(30), TableCell(50)],
        ]
        self.assertEqual(
            analytics.management_report._get_totals(table, 0).value,
            40
        )
        self.assertEqual(
            analytics.management_report._get_totals(table, 1).value,
            70
        )

    def test_get_change(self):
        accounts = {
            'this_month': set([1, 2, 3]),
            'prev_month': set([1, 2, 3, 4, 5]),

            'this_week': set([1, 2, 3, 4]),
            'prev_week': set([3, 5]),
        }
        self.assertEqual(
            analytics.management_report._get_change('month', accounts, set([1, 2, 3, 4, 5])),
            -2
        )
        self.assertEqual(
            analytics.management_report._get_change('week', accounts, set([1, 2, 3, 4, 5])),
            2
        )
        self.assertEqual(
            analytics.management_report._get_change('week', accounts, set([3, 5])),
            -1
        )

    def test_get_counts(self):
        accounts = {
            'this_month': set([1, 2, 3]),
            'prev_month': set([1, 2, 3, 4, 5]),

            'this_week': set([1, 2, 3, 4]),
            'prev_week': set([3, 5]),

            'this_day': set([1, 2]),
            'prev_day': set([3, ]),
        }
        cell = analytics.management_report._get_counts(accounts, set([1, 2, 3, 4, 5]))
        self.assertEqual(
            cell.as_html(),
            '<td>3 (<b>+1</b>, <b>+2</b>, <b>-2</b>)</td>',
        )
        self.assertEqual(
            cell.value,
            3,
        )
        self.assertEqual(
            cell.info,
            [1, 2, -2],
        )

        cell = analytics.management_report._get_counts(accounts, set([1, 2, 3, 4, 5]), total_only=True)
        self.assertEqual(
            cell.as_html(),
            '<td>3</td>',
        )

    def test_populate_agency(self):
        row1 = TableRow(analytics.management_report._populate_agency(self.context, 1))
        self.assertEqual(
            row1.as_html(),
            '<tr><td>1 (<span>0</span>, <span>0</span>, <b>+1</b>)</td><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>$0</td><td>$0</td><td>$0 *</td><td>$0 *</td></tr>'
        )
        row2 = TableRow(analytics.management_report._populate_agency(self.context, 2))
        self.assertEqual(
            row2.as_html(),
            '<tr><td>1 (<b>+1</b>, <span>0</span>, <span>0</span>)</td><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>$0</td><td>$0</td><td>$0 *</td><td>$0 *</td></tr>'
        )
        row3 = TableRow(analytics.management_report._populate_agency(self.context, 6))
        self.assertEqual(
            row3.as_html(),
            '<tr><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>$0</td><td>$0</td><td>$0</td><td>$0</td></tr>'
        )

    def test_populate_clientdirect(self):
        row1 = TableRow(analytics.management_report._populate_clientdirect(self.context, 3))
        self.assertEqual(
            row1.as_html(),
            '<tr><td>2 (<span>0</span>, <b>+2</b>, <b>+1</b>)</td><td>1 (<b>+1</b>, <span>0</span>, <span>0</span>)</td><td>$0</td><td>$0</td><td>$0 *</td><td>$0 *</td></tr>'
        )
        row2 = TableRow(analytics.management_report._populate_clientdirect(self.context, 4))
        self.assertEqual(
            row2.as_html(),
            '<tr><td>1 (<span>0</span>, <span>0</span>, <b>+1</b>)</td><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>$0</td><td>$0</td><td>$0 *</td><td>$0 *</td></tr>'
        )
        row3 = TableRow(analytics.management_report._populate_clientdirect(self.context, 6))
        self.assertEqual(
            row3.as_html(),
            '<tr><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>0 (<span>0</span>, <span>0</span>, <span>0</span>)</td><td>$0</td><td>$0</td><td>$0</td><td>$0</td></tr>'
        )
