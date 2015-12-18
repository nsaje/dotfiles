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
        self.assertEqual(1500000000000, statements[0].media_spend_nano)
        self.assertEqual(500000000000, statements[0].data_spend_nano)
        self.assertEqual(400000000000, statements[0].license_fee_nano)

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
        self.assertEqual(Decimal('0'), statements[0].media_spend_nano)
        self.assertEqual(Decimal('0'), statements[0].data_spend_nano)
        self.assertEqual(Decimal('0'), statements[0].license_fee_nano)

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
            self.assertEqual(0, statement.media_spend_nano)
            self.assertEqual(0, statement.data_spend_nano)
            self.assertEqual(0, statement.license_fee_nano)
        self.assertEqual(1, statements[29].budget_id)
        self.assertEqual(datetime.date(2015, 11, 20), statements[29].date)
        self.assertEqual(2500000000000, statements[29].media_spend_nano)
        self.assertEqual(0, statements[29].data_spend_nano)
        self.assertEqual(500000000000, statements[29].license_fee_nano)
        self.assertEqual(2, statements[30].budget_id)
        self.assertEqual(datetime.date(2015, 11, 20), statements[30].date)
        self.assertEqual(1000000000000, statements[30].media_spend_nano)
        self.assertEqual(500000000000, statements[30].data_spend_nano)
        self.assertEqual(300000000000, statements[30].license_fee_nano)
        self.assertEqual(3, statements[31].budget_id)
        self.assertEqual(datetime.date(2015, 11, 20), statements[31].date)
        self.assertEqual(0, statements[31].media_spend_nano)
        self.assertEqual(0, statements[31].data_spend_nano)
        self.assertEqual(0, statements[31].license_fee_nano)

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
        self.assertEqual(2500000000000, statements[0].media_spend_nano)
        self.assertEqual(0, statements[0].data_spend_nano)
        self.assertEqual(500000000000, statements[0].license_fee_nano)

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
        self.assertEqual(4250000000000, statements[0].media_spend_nano)
        self.assertEqual(0, statements[0].data_spend_nano)
        self.assertEqual(850000000000, statements[0].license_fee_nano)
        self.assertEqual(5, statements[1].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[1].date)
        self.assertEqual(0, statements[1].media_spend_nano)
        self.assertEqual(500000000000, statements[1].data_spend_nano)
        self.assertEqual(500000000000, statements[1].license_fee_nano)

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
            self.assertEqual(0, statement.media_spend_nano)
            self.assertEqual(0, statement.data_spend_nano)
            self.assertEqual(0, statement.license_fee_nano)
            self.assertGreater(datetime.date(2015, 11, 11), statement.date)
        self.assertEqual(1, statements[9].budget_id)
        self.assertEqual(datetime.date(2015, 11, 10), statements[9].date)
        self.assertEqual(2500000000000, statements[9].media_spend_nano)
        self.assertEqual(0, statements[9].data_spend_nano)
        self.assertEqual(500000000000, statements[9].license_fee_nano)
        self.assertEqual(2, statements[10].budget_id)
        self.assertEqual(datetime.date(2015, 11, 10), statements[10].date)
        self.assertEqual(0, statements[10].media_spend_nano)
        self.assertEqual(500000000000, statements[10].data_spend_nano)
        self.assertEqual(100000000000, statements[10].license_fee_nano)
        self.assertEqual(1, statements[11].budget_id)
        self.assertEqual(datetime.date(2015, 11, 11), statements[11].date)
        self.assertEqual(0, statements[11].media_spend_nano)
        self.assertEqual(0, statements[11].data_spend_nano)
        self.assertEqual(0, statements[11].license_fee_nano)
        self.assertEqual(2, statements[12].budget_id)
        self.assertEqual(datetime.date(2015, 11, 11), statements[12].date)
        self.assertEqual(1000000000000, statements[12].media_spend_nano)
        self.assertEqual(0, statements[12].data_spend_nano)
        self.assertEqual(200000000000, statements[12].license_fee_nano)

    def test_max_dates_till_today(self, mock_content_ad_stats, mock_datetime):
        # check that there's no endless loop when update_from is less than all budget start dates
        return_values = {}
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 10, 31, 12))

        self.assertTrue(datetime.date(2015, 11, 1),
                        min(budget.start_date for budget in dash.models.BudgetLineItem.objects.all()))

        update_from = datetime.date(2015, 10, 31)
        dates = daily_statements._get_dates(update_from, self.campaign1)
        self.assertItemsEqual([], dates)

    @patch('reports.daily_statements._generate_statements')
    def test_daily_statements_already_exist(self, mock_generate_statements, mock_content_ad_stats, mock_datetime):
        return_values = {}
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 30, 12))

        for date in [datetime.date(2015, 11, 1) + datetime.timedelta(days=i) for i in range(30)]:
            for budget in dash.models.BudgetLineItem.objects.filter(campaign_id=self.campaign1.id):
                if budget.start_date <= date and budget.end_date >= date:
                    reports.models.BudgetDailyStatement.objects.create(
                        budget_id=budget.id,
                        date=date,
                        media_spend_nano=0,
                        data_spend_nano=0,
                        license_fee_nano=0
                    )

        update_from = datetime.date(2015, 11, 30)
        dates = daily_statements._get_dates(update_from, self.campaign1)
        self.assertItemsEqual([datetime.date(2015, 11, 30)], dates)

        daily_statements.reprocess_daily_statements(update_from, self.campaign1)
        mock_generate_statements.assert_called_once_with(datetime.date(2015, 11, 30), self.campaign1)

    @patch('reports.daily_statements._generate_statements')
    def test_daily_statements_dont_exist(self, mock_generate_statements, mock_content_ad_stats, mock_datetime):
        return_values = {}
        self._configure_content_ad_stats_mock(mock_content_ad_stats, return_values)
        self._configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 30, 12))

        update_from = datetime.date(2015, 11, 30)
        dates = daily_statements._get_dates(update_from, self.campaign1)
        expected_dates = [datetime.date(2015, 11, 1) + datetime.timedelta(days=i) for i in range(30)]
        self.assertItemsEqual(expected_dates, dates)

        daily_statements.reprocess_daily_statements(update_from, self.campaign1)
        expected_calls = [call(x, y) for x, y in itertools.product(expected_dates, [self.campaign1])]
        mock_generate_statements.assert_has_calls(expected_calls)
