import datetime
from decimal import Decimal
from django.test import TestCase
import mock

from dash.models import BudgetLineItem, BudgetDailyStatement
import dash.constants
from analytics import monitor
from utils import converters
import utils.dates_helper


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
            []
        )
        self.assertEqual(
            monitor.audit_spend_patterns(datetime.date(2015, 11, 1)),
            []
        )
        alarms = monitor.audit_spend_patterns(
            datetime.date(2015, 11, 1), first_in_month_threshold=0.9)
        self.assertTrue(alarms)
        self.assertEqual(
            alarms[0][0],
            datetime.date(2015, 11, 1),
        )

    def test_audit_success(self):
        self.assertEqual(
            monitor.audit_spend_patterns(datetime.date(2015, 11, 22)),
            []
        )
        self.assertEqual(
            monitor.audit_spend_patterns(datetime.date(2015, 11, 21), day_range=2),
            []
        )
        self.assertEqual(
            monitor.audit_spend_patterns(datetime.date(2015, 11, 23), threshold=0.2),
            []
        )

    def test_audit_fail(self):
        alarms = monitor.audit_spend_patterns(datetime.date(2015, 11, 22), threshold=1.5)
        self.assertEqual(
            alarms[0][0],
            datetime.date(2015, 11, 22)
        )
        alarms = monitor.audit_spend_patterns(datetime.date(2015, 11, 23))
        self.assertEqual(
            alarms[0][0],
            datetime.date(2015, 11, 23)
        )


class TestAuditSpendPatterns(TestCase):
    fixtures = ['test_projections']

    def setUp(self):
        self.today = datetime.date(2015, 11, 15)

    def _create_statement(self, budget, date, media=500, data=0, margin=0):
        _create_daily_statement(
            date,
            budget,
            media * converters.DOLAR_TO_NANO,
            data_nano=data * converters.DOLAR_TO_NANO,
            margin_nano=margin * converters.DOLAR_TO_NANO,
        )

    def _create_batch_statements(self, budgets, start_date, end_date=None, media=500):
        for date in utils.dates_helper.date_range(start_date, end_date or self.today):
            for budget in budgets:
                if budget.state(date) != dash.constants.BudgetLineItemState.ACTIVE:
                    continue
                self._create_statement(budget, date, media=media)

    def test_normal_pacing(self):
        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 12)

        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date,
            end_date,
        )
        alarms = monitor.audit_pacing(start_date + datetime.timedelta(5))
        self.assertFalse(alarms)

    def test_high_pacing(self):
        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 12)

        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date,
            end_date,
            media=10000,
        )
        alarms = monitor.audit_pacing(start_date + datetime.timedelta(5))

        self.assertTrue(alarms)
        self.assertEqual(
            map(lambda row: row[:3], alarms),
            [(1, Decimal('209.0164'), 'high'),
             (2, Decimal('307.6923'), 'high'), ]
        )

    def test_low_pacing(self):
        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 12)

        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date,
            end_date,
            media=10,
        )
        alarms = monitor.audit_pacing(start_date + datetime.timedelta(5))

        self.assertTrue(alarms)
        self.assertEqual(
            map(lambda row: row[:3], alarms),
            [(1, Decimal('2.2992'), 'low'),
             (2, Decimal('3.3846'), 'low')]
        )


class AuditSpendIntegrity(TestCase):
    fixtures = ['test_projections']

    def setUp(self):
        self.date = datetime.date(2015, 10, 29)
        _create_daily_statement(
            self.date,
            BudgetLineItem.objects.get(pk=2),
            900 * 10**9
        )

    @mock.patch('analytics.monitor._get_rs_spend')
    def test_audit_success(self, mock_rs_spend):
        mock_rs_spend.return_value = {
            'media': 900000000000, 'data': 0, 'fee': 1125000000000, 'margin': 0
        }
        alarms = monitor.audit_spend_integrity(self.date)
        self.assertFalse(alarms)

    @mock.patch('analytics.monitor._get_rs_spend')
    def test_audit_success_with_err(self, mock_rs_spend):
        mock_rs_spend.return_value = {
            'media': 900000070000, 'data': 0, 'fee': 1125000000300, 'margin': 0
        }
        alarms = monitor.audit_spend_integrity(self.date)
        self.assertFalse(alarms)

    @mock.patch('analytics.monitor._get_rs_spend')
    def test_audit_fail(self, mock_rs_spend):
        mock_rs_spend.return_value = {
            'media': 900000000000, 'data': 0, 'fee': 1145000000000, 'margin': 0
        }
        alarms = monitor.audit_spend_integrity(self.date)
        self.assertTrue(alarms)
        self.assertEqual(alarms, [
            (datetime.date(2015, 10, 29), 'mv_master', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_content_ad_delivery_geo', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_content_ad_delivery_demo', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_ad_group_delivery_geo', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_ad_group_delivery_demo', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_campaign_delivery_geo', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_campaign_delivery_demo', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_account_delivery_geo', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_account_delivery_demo', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_content_ad', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_ad_group', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_campaign', 'fee', -20000000000),
            (datetime.date(2015, 10, 29), 'mv_account', 'fee', -20000000000)])


class AuditIABCategories(TestCase):
    fixtures = ['test_projections']

    def test_audit_iab_categories(self):
        self.assertEqual(set(c.pk for c in monitor.audit_iab_categories()), set([
            1, 2,
        ]))
