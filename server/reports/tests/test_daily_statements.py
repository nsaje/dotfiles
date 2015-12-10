import datetime
from decimal import Decimal
from mock import patch, MagicMock, call
import itertools

from django.test import TestCase

import dash.models
from reports import daily_statements
import reports.models


@patch('reports.daily_statements.datetime')
@patch('reports.models.ContentAdStats')
class DailyStatementsTestCase(TestCase):

    fixtures = ['test_daily_statements.yaml']

    def setUp(self):
        self.campaign1 = dash.models.Campaign.objects.get(id=1)
        self.campaign2 = dash.models.Campaign.objects.get(id=2)

    def _configure_content_ad_stats_mock(self, mock_content_ad_stats, return_values):
        def fn(date, *args, **kwargs):
            ret = {'cost_cc_sum': 0, 'data_cost_cc_sum': 0}
            if date in return_values:
                ret = return_values[date]
            return MagicMock(**{'aggregate.return_value': ret})
        mock_content_ad_stats.configure_mock(**{'objects.filter.side_effect': fn})

    def _configure_datetime_utcnow_mock(self, mock_datetime, utcnow_value):
        class DatetimeMock(datetime.datetime):
            @classmethod
            def utcnow(cls):
                return utcnow_value

        mock_datetime.datetime = DatetimeMock
        mock_datetime.timedelta = datetime.timedelta

    def test_first_day_single_daily_statemnt(self, mock_content_ad_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 1): {
                'cost_cc_sum': 15000000,
                'data_cost_cc_sum': 5000000,
            }
        }
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 1, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from, self.campaign1)

        statements = reports.models.BudgetDailyStatement.objects.all()
        self.assertEqual(1, len(statements))
        self.assertEqual(1, statements[0].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[0].date)
        self.assertEqual(Decimal('2400.0'), statements[0].spend)

    def test_first_day_cost_none(self, mock_content_ad_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 1): {
                'cost_cc_sum': None,
                'data_cost_cc_sum': None,
            }
        }
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 1, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from, self.campaign1)

        statements = reports.models.BudgetDailyStatement.objects.all()
        self.assertEqual(1, len(statements))
        self.assertEqual(1, statements[0].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[0].date)
        self.assertEqual(Decimal('0'), statements[0].spend)

    def test_multiple_budgets_attribution_order(self, mock_content_ad_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 20): {
                'cost_cc_sum': 35000000,
                'data_cost_cc_sum': 5000000,
            }
        }
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 20, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from, self.campaign1)
        statements = reports.models.BudgetDailyStatement.objects.all().order_by('date', 'budget_id')
        self.assertEqual(32, len(statements))
        for statement in statements[:29]:
            self.assertGreater(datetime.date(2015, 11, 20), statement.date)
            self.assertEqual(0, statement.spend)
        self.assertEqual(1, statements[29].budget_id)
        self.assertEqual(datetime.date(2015, 11, 20), statements[29].date)
        self.assertEqual(Decimal('3000'), statements[29].spend)
        self.assertEqual(2, statements[30].budget_id)
        self.assertEqual(datetime.date(2015, 11, 20), statements[30].date)
        self.assertEqual(Decimal('1800'), statements[30].spend)
        self.assertEqual(3, statements[31].budget_id)
        self.assertEqual(datetime.date(2015, 11, 20), statements[31].date)
        self.assertEqual(Decimal('0'), statements[31].spend)

    def test_overspend(self, mock_content_ad_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 1): {
                'cost_cc_sum': 30000000,
                'data_cost_cc_sum': 5000000,
            }
        }
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 1, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from, self.campaign1)
        statements = reports.models.BudgetDailyStatement.objects.all().order_by('date', 'budget_id')
        self.assertEqual(1, len(statements))
        self.assertEqual(1, statements[0].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[0].date)
        self.assertEqual(Decimal('3000.0'), statements[0].spend)

    def test_different_fees(self, mock_content_ad_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 1): {
                'cost_cc_sum': 42500000,
                'data_cost_cc_sum': 5000000,
            }
        }
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 1, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from, self.campaign2)
        statements = reports.models.BudgetDailyStatement.objects.all().order_by('date', 'budget_id')
        self.assertEqual(2, len(statements))
        self.assertEqual(4, statements[0].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[0].date)
        self.assertEqual(Decimal('5100.0'), statements[0].spend)
        self.assertEqual(5, statements[1].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[1].date)
        self.assertEqual(Decimal('1000.0'), statements[1].spend)

    def test_different_days(self, mock_content_ad_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 10): {
                'cost_cc_sum': 25000000,
                'data_cost_cc_sum': 5000000,
            },
            datetime.date(2015, 11, 11): {
                'cost_cc_sum': 10000000,
                'data_cost_cc_sum': 0,
            }
        }
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 11, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from, self.campaign1)
        statements = reports.models.BudgetDailyStatement.objects.all().order_by('date', 'budget_id')
        self.assertEqual(13, len(statements))
        for statement in statements[:9]:
            self.assertEqual(0, statement.spend)
            self.assertGreater(datetime.date(2015, 11, 11), statement.date)
        self.assertEqual(1, statements[9].budget_id)
        self.assertEqual(datetime.date(2015, 11, 10), statements[9].date)
        self.assertEqual(Decimal('3000.0'), statements[9].spend)
        self.assertEqual(2, statements[10].budget_id)
        self.assertEqual(datetime.date(2015, 11, 10), statements[10].date)
        self.assertEqual(Decimal('600.0'), statements[10].spend)
        self.assertEqual(1, statements[11].budget_id)
        self.assertEqual(datetime.date(2015, 11, 11), statements[11].date)
        self.assertEqual(Decimal('0'), statements[11].spend)
        self.assertEqual(2, statements[12].budget_id)
        self.assertEqual(datetime.date(2015, 11, 11), statements[12].date)
        self.assertEqual(Decimal('1200.0'), statements[12].spend)

    @patch('reports.daily_statements._generate_statement')
    def test_daily_statements_already_exist(self, mock_generate_statement, mock_content_ad_stats, mock_datetime):
        return_values = {}
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 30, 12))

        for date in [datetime.date(2015, 11, 1) + datetime.timedelta(days=i) for i in range(30)]:
            for budget in dash.models.BudgetLineItem.objects.filter(campaign_id=self.campaign1.id):
                if budget.start_date <= date and budget.end_date >= date:
                    reports.models.BudgetDailyStatement.objects.create(
                        budget_id=budget.id,
                        date=date,
                        spend=0
                    )

        update_from = datetime.date(2015, 11, 30)
        dates = daily_statements._get_dates(update_from, self.campaign1)
        self.assertItemsEqual([datetime.date(2015, 11, 30)], dates)

        daily_statements.reprocess_daily_statements(update_from, self.campaign1)
        mock_generate_statement.assert_called_once_with(datetime.date(2015, 11, 30), self.campaign1)

    @patch('reports.daily_statements._generate_statement')
    def test_daily_statements_dont_exist(self, mock_generate_statement, mock_content_ad_stats, mock_datetime):
        return_values = {}
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 30, 12))

        update_from = datetime.date(2015, 11, 30)
        dates = daily_statements._get_dates(update_from, self.campaign1)
        expected_dates = [datetime.date(2015, 11, 1) + datetime.timedelta(days=i) for i in range(30)]
        self.assertItemsEqual(expected_dates, dates)

        daily_statements.reprocess_daily_statements(update_from, self.campaign1)
        expected_calls = [call(x, y) for x, y in itertools.product(expected_dates, [self.campaign1])]
        mock_generate_statement.assert_has_calls(expected_calls)
