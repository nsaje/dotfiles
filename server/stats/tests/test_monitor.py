import datetime
import mock
from django.test import TestCase


from dash.models import BudgetLineItem
from reports.models import BudgetDailyStatement

from stats import monitor


def _create_daily_statement(date, budget, media_nano, data_nano=0, margin_nano=0):
    BudgetDailyStatement.objects.create(
        date=date,
        budget=budget,
        media_spend_nano=media_nano,
        data_spend_nano=data_nano,
        license_fee_nano=int(media_nano / (1 - budget.credit.license_fee)),
        margin_nano=margin_nano,
    )


class AuditSpendPatternsTest(TestCase):
    fixtures = ['test_projections']

    def setUp(self):
        _create_daily_statement(
            datetime.date(2015, 10, 29),
            BudgetLineItem.objects.get(pk=2),
            900 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 10, 30),
            BudgetLineItem.objects.get(pk=2),
            1000 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 10, 31),
            BudgetLineItem.objects.get(pk=2),
            950 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 11, 1),
            BudgetLineItem.objects.get(pk=2),
            650 * 10**9
        )

        _create_daily_statement(
            datetime.date(2015, 11, 19),
            BudgetLineItem.objects.get(pk=4),
            900 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 11, 20),
            BudgetLineItem.objects.get(pk=3),
            900 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 11, 21),
            BudgetLineItem.objects.get(pk=3),
            1100 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 11, 22),
            BudgetLineItem.objects.get(pk=3),
            750 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 11, 23),
            BudgetLineItem.objects.get(pk=3),
            800 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 11, 20),
            BudgetLineItem.objects.get(pk=5),
            900 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 11, 21),
            BudgetLineItem.objects.get(pk=5),
            1100 * 10**9
        )
        _create_daily_statement(
            datetime.date(2015, 11, 22),
            BudgetLineItem.objects.get(pk=5),
            1000 * 10**9
        )

    def test_audit_first_in_month(self):
        self.assertEqual(
            monitor.audit_spend_patterns(datetime.date(2015, 10, 31)),
            (True, [])
        )
        self.assertEqual(
            monitor.audit_spend_patterns(datetime.date(2015, 11, 1)),
            (True, [])
        )
        status, info = monitor.audit_spend_patterns(
            datetime.date(2015, 11, 1), first_in_month_threshold=0.9)
        self.assertFalse(status)
        self.assertEqual(
            info[0][0],
            datetime.date(2015, 11, 1),
        )

    def test_audit_success(self):
        self.assertEqual(
            monitor.audit_spend_patterns(datetime.date(2015, 11, 22)),
            (True, [])
        )
        self.assertEqual(
            monitor.audit_spend_patterns(datetime.date(2015, 11, 21), day_range=2),
            (True, [])
        )
        self.assertEqual(
            monitor.audit_spend_patterns(datetime.date(2015, 11, 23), threshold=0.2),
            (True, [])
        )

    def test_audit_fail(self):
        status, info = monitor.audit_spend_patterns(datetime.date(2015, 11, 22), threshold=1.5)
        self.assertEqual(
            info[0][0],
            datetime.date(2015, 11, 22)
        )
        status, info = monitor.audit_spend_patterns(datetime.date(2015, 11, 23))
        self.assertEqual(
            info[0][0],
            datetime.date(2015, 11, 23)
        )
