import datetime
from decimal import Decimal
from mock import patch

from django.test import TestCase
from django.db.models import Max

import core.bcm
import core.entity
import core.multicurrency
import dash.models
import dash.constants
from etl import daily_statements_k1 as daily_statements
from utils import converters
from utils import test_helper
from utils.magic_mixer import magic_mixer


def _configure_ad_group_stats_mock(mock_ad_group_stats, return_values):
    def f(date, all_campaigns, account_id):
        return return_values.get(date, {})
    mock_ad_group_stats.configure_mock(**{'side_effect': f})


def _configure_datetime_utcnow_mock(mock_datetime, utcnow_value):
    class DatetimeMock(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return utcnow_value

    mock_datetime.datetime = DatetimeMock
    mock_datetime.timedelta = datetime.timedelta


class MultiCurrencyTestCase(TestCase):

    def setUp(self):
        self.mock_today = datetime.date(2018, 3, 1)
        account = magic_mixer.blend(core.entity.Account, currency=dash.constants.Currency.EUR)
        self.campaign = magic_mixer.blend(core.entity.Campaign, account=account)
        self.credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=self.campaign.account,
            start_date=self.mock_today,
            end_date=self.mock_today,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=500,
            license_fee=Decimal('0.135'),
            currency=dash.constants.Currency.EUR,
        )
        self.budget = magic_mixer.blend(
            core.bcm.BudgetLineItem,
            credit=self.credit,
            campaign=self.campaign,
            start_date=self.mock_today,
            end_date=self.mock_today,
            amount=500,
            margin=Decimal('0.22'),
        )

        self.exchange_rate = Decimal('0.8187')
        core.multicurrency.CurrencyExchangeRate.objects.create(
            date=self.mock_today,
            currency=dash.constants.Currency.EUR,
            exchange_rate=self.exchange_rate,
        )

    @patch('utils.dates_helper.datetime')
    @patch('etl.daily_statements_k1._get_campaign_spend')
    @patch('etl.daily_statements_k1.get_campaigns_with_spend', return_value=dash.models.Campaign.objects.none())
    def test_non_usd_currency(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            self.mock_today: {
                self.campaign.id: {
                    'media_nano': 350 * 10**9,
                    'data_nano': 150 * 10**9,
                },
            },
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day, 12))

        daily_statements.reprocess_daily_statements(self.mock_today)
        statement = core.bcm.BudgetDailyStatement.objects.get(budget=self.budget)

        self.assertEqual(Decimal('350.0') * 10**9, statement.media_spend_nano)
        self.assertEqual(Decimal('62.055698057') * 10**9, statement.data_spend_nano)
        self.assertEqual(Decimal('64.309270795') * 10**9, statement.license_fee_nano)
        self.assertEqual(Decimal('134.359350189') * 10**9, statement.margin_nano)
        self.assertAlmostEqual(
            self.budget.amount / self.exchange_rate,
            (statement.media_spend_nano + statement.data_spend_nano +
             statement.license_fee_nano + statement.margin_nano) / Decimal(10**9),
            delta=Decimal('0.0001')
        )

        self.assertEqual(Decimal('286.545') * 10**9, statement.local_media_spend_nano)
        self.assertEqual(Decimal('50.805') * 10**9, statement.local_data_spend_nano)
        self.assertEqual(Decimal('52.65') * 10**9, statement.local_license_fee_nano)
        self.assertEqual(Decimal('110.0') * 10**9, statement.local_margin_nano)
        self.assertEqual(
            self.budget.amount * 10**9,
            statement.local_media_spend_nano + statement.local_data_spend_nano +
            statement.local_license_fee_nano + statement.local_margin_nano
        )

    # FIXME (multicurrency): Fix the following test so that error "Cannot allocate budget from a credit in currency
    # different from account's currency." is not raised.
    # @patch('utils.dates_helper.datetime')
    # @patch('etl.daily_statements_k1._get_campaign_spend')
    # @patch('etl.daily_statements_k1.get_campaigns_with_spend', return_value=dash.models.Campaign.objects.none())
    # def test_mixed_currencies(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
    #     media_nano = 350
    #     data_nano = 150
    #     return_values = {
    #         self.mock_today: {
    #             self.campaign.id: {
    #                 'media_nano': media_nano * 10**9,
    #                 'data_nano': data_nano * 10**9,
    #             },
    #         },
    #     }
    #     _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
    #     _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(self.mock_today.year, self.mock_today.month, self.mock_today.day, 12))

    #     credit2 = magic_mixer.blend(
    #         core.bcm.CreditLineItem,
    #         account=self.campaign.account,
    #         start_date=self.mock_today,
    #         end_date=self.mock_today,
    #         status=dash.constants.CreditLineItemStatus.SIGNED,
    #         amount=500,
    #         license_fee=Decimal('0.10'),
    #         currency=dash.constants.Currency.USD,
    #     )
    #     budget2 = magic_mixer.blend(
    #         core.bcm.BudgetLineItem,
    #         credit=credit2,
    #         campaign=self.campaign,
    #         start_date=self.mock_today,
    #         end_date=self.mock_today,
    #         amount=500,
    #         margin=Decimal('0.20'),
    #     )

    #     daily_statements.reprocess_daily_statements(self.mock_today)
    #     eur_statement = core.bcm.BudgetDailyStatement.objects.get(budget=self.budget)

    #     self.assertEqual(Decimal('350.0') * 10**9, eur_statement.media_spend_nano)
    #     self.assertEqual(Decimal('62.055698057') * 10**9, eur_statement.data_spend_nano)
    #     self.assertEqual(Decimal('64.309270795') * 10**9, eur_statement.license_fee_nano)
    #     self.assertEqual(Decimal('134.359350189') * 10**9, eur_statement.margin_nano)
    #     self.assertAlmostEqual(
    #         self.budget.amount / self.exchange_rate,
    #         (eur_statement.media_spend_nano + eur_statement.data_spend_nano +
    #          eur_statement.license_fee_nano + eur_statement.margin_nano) / Decimal(10**9),
    #         delta=Decimal('0.0001')
    #     )

    #     self.assertEqual(Decimal('286.545') * 10**9, eur_statement.local_media_spend_nano)
    #     self.assertEqual(Decimal('50.805') * 10**9, eur_statement.local_data_spend_nano)
    #     self.assertEqual(Decimal('52.65') * 10**9, eur_statement.local_license_fee_nano)
    #     self.assertEqual(Decimal('110.0') * 10**9, eur_statement.local_margin_nano)
    #     self.assertEqual(
    #         self.budget.amount * 10**9,
    #         eur_statement.local_media_spend_nano + eur_statement.local_data_spend_nano +
    #         eur_statement.local_license_fee_nano + eur_statement.local_margin_nano
    #     )

    #     usd_statement = core.bcm.BudgetDailyStatement.objects.get(budget=budget2)
    #     self.assertAlmostEqual(
    #         media_nano + data_nano,
    #         Decimal(eur_statement.media_spend_nano + eur_statement.data_spend_nano +
    #                 usd_statement.media_spend_nano + usd_statement.data_spend_nano) / 10**9,
    #         delta=Decimal('0.0001'),
    #     )
    #     self.assertEqual(0, usd_statement.media_spend_nano)
    #     self.assertEqual(Decimal('87.944301942'), usd_statement.data_spend_nano / Decimal(10**9))
    #     self.assertEqual(Decimal('9.771589104'), usd_statement.license_fee_nano / Decimal(10**9))
    #     self.assertEqual(Decimal('24.428972761'), usd_statement.margin_nano / Decimal(10**9))


@patch('utils.dates_helper.datetime')
@patch('etl.daily_statements_k1._get_campaign_spend')
@patch('etl.daily_statements_k1.get_campaigns_with_spend', return_value=dash.models.Campaign.objects.none())
class DailyStatementsK1TestCase(TestCase):

    fixtures = ['test_daily_statements.yaml']

    def setUp(self):
        self.campaign1 = dash.models.Campaign.objects.get(id=1)
        self.campaign2 = dash.models.Campaign.objects.get(id=2)
        self.campaign3 = dash.models.Campaign.objects.get(id=3)

        core.multicurrency.CurrencyExchangeRate.objects.create(
            date='1970-01-01',
            currency=dash.constants.Currency.USD,
            exchange_rate=1,
        )

    def test_first_day_single_daily_statemnt(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 1): {
                self.campaign1.id: {
                    'media_nano': 1500000000000,
                    'data_nano': 500000000000,
                },
            },
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 1, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from)

        statements = dash.models.BudgetDailyStatement.objects.filter(budget__campaign=self.campaign1).all()
        self.assertEqual(1, len(statements))
        self.assertEqual(1, statements[0].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[0].date)
        self.assertEqual(1500000000000, statements[0].media_spend_nano)
        self.assertEqual(500000000000, statements[0].data_spend_nano)
        self.assertEqual(500000000000, statements[0].license_fee_nano)

    def test_budget_margin(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2016, 7, 15): {
                self.campaign3.id: {
                    'media_nano': 1500000000000,
                    'data_nano': 500000000000,
                },
            },
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2016, 7, 15, 12))

        update_from = datetime.date(2016, 7, 15)
        daily_statements.reprocess_daily_statements(update_from)

        statements = dash.models.BudgetDailyStatement.objects.filter(budget__campaign=self.campaign3).all()
        self.assertEqual(1, len(statements))
        self.assertEqual(6, statements[0].budget_id)
        self.assertEqual(datetime.date(2016, 7, 15), statements[0].date)
        self.assertEqual(1500000000000, statements[0].media_spend_nano)
        self.assertEqual(500000000000, statements[0].data_spend_nano)
        self.assertEqual(500000000000, statements[0].license_fee_nano)
        self.assertEqual(250000000000, statements[0].margin_nano)

    def test_budget_with_fixed_margin(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2017, 6, 21): {
                self.campaign3.id: {
                    'media_nano': 1000000000000,
                    'data_nano': 360000000000,
                },
            },
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2017, 6, 21, 12))

        update_from = datetime.date(2017, 6, 21)
        daily_statements.reprocess_daily_statements(update_from)

        statements = dash.models.BudgetDailyStatement.objects.filter(
            budget__campaign=self.campaign3).order_by('-date')
        self.assertEqual(7, statements[0].budget_id)
        self.assertEqual(datetime.date(2017, 6, 21), statements[0].date)

        statement = statements[0]
        # $1000 media + $360 data + $340 fee = $1700; $1700 == $2000 * 85% (margin pct)
        self.assertEqual(1000, statement.media_spend_nano / 10**9)
        self.assertEqual(360, statement.data_spend_nano / 10**9)
        self.assertEqual(340, statement.license_fee_nano / 10**9)
        self.assertEqual(300, statement.margin_nano / 10**9)

    def test_budget_with_fixed_margin_overspend(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2017, 6, 21): {
                self.campaign3.id: {
                    'media_nano': 480 * 10**9,
                    'data_nano': 200 * 10**9,
                },
            },
            datetime.date(2017, 6, 22): {
                self.campaign3.id: {
                    'media_nano': 1000 * 10**9,
                    'data_nano': 400 * 10**9,
                },
            },
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2017, 6, 22, 12))

        update_from = datetime.date(2017, 6, 21)
        daily_statements.reprocess_daily_statements(update_from)

        statements = dash.models.BudgetDailyStatement.objects.filter(
            budget_id=7).order_by('date')
        self.assertEqual(datetime.date(2017, 6, 21), statements[0].date)

        statement1 = statements[0]
        self.assertEqual(datetime.date(2017, 6, 21), statement1.date)

        # $480 media + $200 data + $170 fee = $850; $850 == $1000 * 85% (margin pct)
        # budget spent: $1000/$3000
        self.assertEqual(480, statement1.media_spend_nano / 10**9)
        self.assertEqual(200, statement1.data_spend_nano / 10**9)
        self.assertEqual(170, statement1.license_fee_nano / 10**9)
        self.assertEqual(150, statement1.margin_nano / 10**9)

        statement2 = statements[1]
        self.assertEqual(datetime.date(2017, 6, 22), statement2.date)

        # $1000 media + $360 data + $340 fee = $1700; $1700 == $2000 * 85% (margin pct)
        # budget spent: $3000 / $3000
        # overspend: $120
        self.assertEqual(1000, statement2.media_spend_nano / 10**9)
        self.assertEqual(360, statement2.data_spend_nano / 10**9)
        self.assertEqual(340, statement2.license_fee_nano / 10**9)
        self.assertEqual(300, statement2.margin_nano / 10**9)

        self.assertEqual(
            statement2.budget.amount,
            (statement1.media_spend_nano + statement1.data_spend_nano +
             statement1.license_fee_nano + statement1.margin_nano +
             statement2.media_spend_nano + statement2.data_spend_nano +
             statement2.license_fee_nano + statement2.margin_nano) / 10**9)

    def test_first_day_cost_none(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {}
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 1, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from)

        statements = dash.models.BudgetDailyStatement.objects.filter(budget__campaign=self.campaign1).all()
        self.assertEqual(1, len(statements))
        self.assertEqual(1, statements[0].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[0].date)
        self.assertEqual(Decimal('0'), statements[0].media_spend_nano)
        self.assertEqual(Decimal('0'), statements[0].data_spend_nano)
        self.assertEqual(Decimal('0'), statements[0].license_fee_nano)

    def test_multiple_budgets_attribution_order(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 20): {
                self.campaign1.id: {
                    'media_nano': 3500000000000,
                    'data_nano': 500000000000,
                },
            }
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 20, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from)
        statements = (
            dash.models.BudgetDailyStatement.objects.
            filter(budget__campaign=self.campaign1).
            all().
            order_by('date', 'budget_id')
        )
        self.assertEqual(32, len(statements))
        for statement in statements[:29]:
            self.assertGreater(datetime.date(2015, 11, 20), statement.date)
            self.assertEqual(0, statement.media_spend_nano)
            self.assertEqual(0, statement.data_spend_nano)
            self.assertEqual(0, statement.license_fee_nano)

        self.assertEqual(1, statements[29].budget_id)
        self.assertEqual(datetime.date(2015, 11, 20), statements[29].date)
        self.assertEqual(2400000000000, statements[29].media_spend_nano)
        self.assertEqual(0, statements[29].data_spend_nano)
        self.assertEqual(600000000000, statements[29].license_fee_nano)
        self.assertEqual(2, statements[30].budget_id)
        self.assertEqual(datetime.date(2015, 11, 20), statements[30].date)
        self.assertEqual(1100000000000, statements[30].media_spend_nano)
        self.assertEqual(500000000000, statements[30].data_spend_nano)
        self.assertEqual(400000000000, statements[30].license_fee_nano)
        self.assertEqual(3, statements[31].budget_id)
        self.assertEqual(datetime.date(2015, 11, 20), statements[31].date)
        self.assertEqual(0, statements[31].media_spend_nano)
        self.assertEqual(0, statements[31].data_spend_nano)
        self.assertEqual(0, statements[31].license_fee_nano)

    def test_overspend_with_campaign_stop(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 1): {
                self.campaign1.id: {
                    'media_nano': 3000000000000,
                    'data_nano': 500000000000,
                }
            }
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 1, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from)
        statements = (
            dash.models.BudgetDailyStatement.objects.
            filter(budget__campaign=self.campaign1).
            all().
            order_by('date', 'budget_id')
        )
        self.assertEqual(1, len(statements))
        self.assertEqual(1, statements[0].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[0].date)
        self.assertEqual(2400000000000, statements[0].media_spend_nano)
        self.assertEqual(0, statements[0].data_spend_nano)
        self.assertEqual(600000000000, statements[0].license_fee_nano)

    def test_overspend_manual(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 1): {
                self.campaign1.id: {
                    'media_nano': 3000000000000,
                    'data_nano': 500000000000,
                }
            }
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 1, 12))

        self.campaign1.settings.update(None, automatic_campaign_stop=False)

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from)
        statements = (
            dash.models.BudgetDailyStatement.objects.
            filter(budget__campaign=self.campaign1).
            all().
            order_by('date', 'budget_id')
        )
        self.assertEqual(1, len(statements))
        self.assertEqual(1, statements[0].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[0].date)
        self.assertEqual(3000000000000, statements[0].media_spend_nano)
        self.assertEqual(500000000000, statements[0].data_spend_nano)
        self.assertEqual(875000000000, statements[0].license_fee_nano)

    def test_overspend_manual_no_budget(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 10, 1): {
                self.campaign1.id: {
                    'media_nano': 3000000000000,
                    'data_nano': 500000000000,
                }
            }
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 10, 1, 12))

        dash.models.CreditLineItem.objects.create_unsafe(
            account_id=self.campaign1.id,
            start_date=datetime.date(2015, 10, 1),
            end_date=datetime.date(2015, 10, 1),
            amount=0,
            license_fee=Decimal('0.2'),
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        self.campaign1.settings.update(None, automatic_campaign_stop=False)

        update_from = datetime.date(2015, 10, 1)
        daily_statements.reprocess_daily_statements(update_from)
        statements = (
            dash.models.BudgetDailyStatement.objects.
            filter(budget__campaign=self.campaign1).
            all().
            order_by('date', 'budget_id')
        )
        self.assertEqual(1, len(statements))
        self.assertEqual(0, statements[0].budget.amount)
        self.assertEqual(datetime.date(2015, 10, 1), statements[0].budget.start_date)
        self.assertEqual(datetime.date(2015, 10, 1), statements[0].budget.end_date)
        self.assertEqual(datetime.date(2015, 10, 1), statements[0].date)
        self.assertEqual(3000000000000, statements[0].media_spend_nano)
        self.assertEqual(500000000000, statements[0].data_spend_nano)
        self.assertEqual(875000000000, statements[0].license_fee_nano)

    def test_different_fees(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 1): {
                self.campaign2.id: {
                    'media_nano': 4000000000000,
                    'data_nano': 500000000000,
                }
            }
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 1, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from)
        statements = (
            dash.models.BudgetDailyStatement.objects.
            filter(budget__campaign=self.campaign2).
            all().
            order_by('date', 'budget_id')
        )
        self.assertEqual(2, len(statements))
        self.assertEqual(4, statements[0].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[0].date)
        self.assertEqual(4000000000000, statements[0].media_spend_nano)
        self.assertEqual(0, statements[0].data_spend_nano)
        self.assertEqual(1000000000000, statements[0].license_fee_nano)
        self.assertEqual(5, statements[1].budget_id)
        self.assertEqual(datetime.date(2015, 11, 1), statements[1].date)
        self.assertEqual(0, statements[1].media_spend_nano)
        self.assertEqual(500000000000, statements[1].data_spend_nano)
        self.assertEqual(500000000000, statements[1].license_fee_nano)

    def test_different_days(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        return_values = {
            datetime.date(2015, 11, 10): {
                self.campaign1.id: {
                    'media_nano': 2500000000000,
                    'data_nano': 500000000000,
                }
            },
            datetime.date(2015, 11, 11): {
                self.campaign1.id: {
                    'media_nano': 1000000000000,
                    'data_nano': 0,
                }
            }
        }
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 11, 12))

        update_from = datetime.date(2015, 11, 1)
        daily_statements.reprocess_daily_statements(update_from)
        statements = (
            dash.models.BudgetDailyStatement.objects.
            filter(budget__campaign=self.campaign1).
            all().
            order_by('date', 'budget_id')
        )
        self.assertEqual(13, len(statements))
        for statement in statements[:9]:
            self.assertEqual(0, statement.media_spend_nano)
            self.assertEqual(0, statement.data_spend_nano)
            self.assertEqual(0, statement.license_fee_nano)
            self.assertGreater(datetime.date(2015, 11, 11), statement.date)
        self.assertEqual(1, statements[9].budget_id)
        self.assertEqual(datetime.date(2015, 11, 10), statements[9].date)
        self.assertEqual(2400000000000, statements[9].media_spend_nano)
        self.assertEqual(0, statements[9].data_spend_nano)
        self.assertEqual(600000000000, statements[9].license_fee_nano)
        self.assertEqual(2, statements[10].budget_id)
        self.assertEqual(datetime.date(2015, 11, 10), statements[10].date)
        self.assertEqual(100000000000, statements[10].media_spend_nano)
        self.assertEqual(500000000000, statements[10].data_spend_nano)
        self.assertEqual(150000000000, statements[10].license_fee_nano)
        self.assertEqual(1, statements[11].budget_id)
        self.assertEqual(datetime.date(2015, 11, 11), statements[11].date)
        self.assertEqual(0, statements[11].media_spend_nano)
        self.assertEqual(0, statements[11].data_spend_nano)
        self.assertEqual(0, statements[11].license_fee_nano)
        self.assertEqual(2, statements[12].budget_id)
        self.assertEqual(datetime.date(2015, 11, 11), statements[12].date)
        self.assertEqual(1000000000000, statements[12].media_spend_nano)
        self.assertEqual(0, statements[12].data_spend_nano)
        self.assertEqual(250000000000, statements[12].license_fee_nano)

    def test_max_dates_till_today(self, mock_campaign_with_spend, mock_ad_group_stats, mock_datetime):
        # check that there's no endless loop when update_from is less than all budget start dates
        return_values = {}
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 10, 31, 12))

        self.assertTrue(datetime.date(2015, 11, 1),
                        min(budget.start_date for budget in dash.models.BudgetLineItem.objects.all()))

        update_from = datetime.date(2015, 10, 31)
        campaigns = (dash.models.Campaign.objects.filter(pk=self.campaign1.id)
                     .annotate(max_budget_end_date=Max('budgets__end_date')))
        first_unprocessed_dates = daily_statements._get_first_unprocessed_dates(campaigns)
        dates = daily_statements._get_dates(update_from, campaigns[0], first_unprocessed_dates.get(self.campaign1.id))
        self.assertCountEqual([update_from], dates)

    @patch('etl.daily_statements_k1._generate_statements')
    def test_daily_statements_already_exist(self, mock_generate_statements, mock_campaign_with_spend,
                                            mock_ad_group_stats, mock_datetime):
        return_values = {}
        _configure_ad_group_stats_mock(mock_ad_group_stats, return_values)
        _configure_datetime_utcnow_mock(mock_datetime, datetime.datetime(2015, 11, 30, 12))

        campaigns = dash.models.Campaign.objects.filter(account_id=1)

        for date in [datetime.date(2015, 11, 1) + datetime.timedelta(days=i) for i in range(30)]:
            for budget in dash.models.BudgetLineItem.objects.filter(campaign__in=campaigns):
                if budget.start_date <= date and budget.end_date >= date:
                    dash.models.BudgetDailyStatement.objects.create(
                        budget=budget,
                        date=date,
                        media_spend_nano=0,
                        data_spend_nano=0,
                        license_fee_nano=0,
                        margin_nano=0,
                    )

        update_from = datetime.date(2015, 11, 30)

        campaigns = campaigns.annotate(max_budget_end_date=Max('budgets__end_date'))
        first_unprocessed_dates = daily_statements._get_first_unprocessed_dates(campaigns)
        for campaign in campaigns:
            dates = daily_statements._get_dates(
                update_from, campaign, first_unprocessed_dates.get(campaign.id))
            self.assertCountEqual([datetime.date(2015, 11, 30)], dates)

        daily_statements.reprocess_daily_statements(update_from, account_id=1)
        self.assertEqual(mock_generate_statements.call_count, len(campaigns))


class EffectiveSpendPctsK1TestCase(TestCase):

    fixtures = ['test_api_contentads.yaml']

    def test_spend(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        budget = dash.models.BudgetLineItem.objects.get(id=1)
        date = datetime.date(2015, 2, 1)

        campaign_spend = {
            'media_nano': 40 * converters.CURRENCY_TO_NANO,
            'data_nano': 40 * converters.CURRENCY_TO_NANO,
        }
        total_spend = {
            date: {
                campaign.id: campaign_spend,
            },
        }
        dash.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=date,
            media_spend_nano=campaign_spend['media_nano'],
            data_spend_nano=campaign_spend['media_nano'],
            license_fee_nano=(campaign_spend['media_nano'] + campaign_spend['data_nano']) * budget.credit.license_fee,
            margin_nano=24 * converters.CURRENCY_TO_NANO,)

        effective_spend = daily_statements._get_effective_spend(None, [date], total_spend)
        pct_actual_spend, pct_license_fee, pct_margin = effective_spend[date][campaign]

        self.assertEqual(Decimal('1'), pct_actual_spend)
        self.assertEqual(Decimal('0.2'), pct_license_fee)
        self.assertEqual(Decimal('0.25'), pct_margin)

    def test_campaign_spend_none(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        date = datetime.date(2015, 2, 1)

        campaign_spend = None
        total_spend = {
            date: {
                campaign.id: campaign_spend,
            },
        }
        effective_spend = daily_statements._get_effective_spend(None, [date], total_spend)

        self.assertEqual(effective_spend[date][campaign], (0, 0, 0))

    def test_overspend_pcts(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        budget = dash.models.BudgetLineItem.objects.get(id=1)
        date = datetime.date(2015, 2, 1)

        campaign_spend = {
            'media_nano': 40 * converters.CURRENCY_TO_NANO,
            'data_nano': 40 * converters.CURRENCY_TO_NANO,
        }
        total_spend = {
            date: {
                campaign.id: campaign_spend,
            },
        }

        attributed_media_spend_nano = (campaign_spend['media_nano']) * Decimal('0.8')
        attributed_data_spend_nano = (campaign_spend['data_nano']) * Decimal('0.8')
        license_fee_nano = (attributed_media_spend_nano + attributed_data_spend_nano) * budget.credit.license_fee

        dash.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=date,
            media_spend_nano=attributed_media_spend_nano,
            data_spend_nano=attributed_data_spend_nano,
            license_fee_nano=license_fee_nano,
            margin_nano=0,
        )

        effective_spend = daily_statements._get_effective_spend(None, [date], total_spend)
        pct_actual_spend, pct_license_fee, pct_margin = effective_spend[date][campaign]

        self.assertEqual(Decimal('0.8'), pct_actual_spend)
        self.assertEqual(Decimal('0.2'), pct_license_fee)

    def test_different_license_fees(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        budget1 = dash.models.BudgetLineItem.objects.get(id=1)
        budget2 = dash.models.BudgetLineItem.objects.get(id=2)
        date = datetime.date(2015, 2, 1)

        campaign_spend = {
            'media_nano': 40 * converters.CURRENCY_TO_NANO,
            'data_nano': 40 * converters.CURRENCY_TO_NANO,
        }
        total_spend = {
            date: {
                campaign.id: campaign_spend,
            },
        }

        attributed_media_spend_nano = (campaign_spend['media_nano']) * Decimal('0.5')
        attributed_data_spend_nano = (campaign_spend['data_nano']) * Decimal('0.5')

        dash.models.BudgetDailyStatement.objects.create(
            budget=budget1,
            date=date,
            media_spend_nano=attributed_media_spend_nano,
            data_spend_nano=attributed_data_spend_nano,
            license_fee_nano=(attributed_media_spend_nano + attributed_data_spend_nano) * budget1.credit.license_fee,
            margin_nano=0,
        )

        dash.models.BudgetDailyStatement.objects.create(
            budget=budget2,
            date=date,
            media_spend_nano=attributed_media_spend_nano,
            data_spend_nano=attributed_data_spend_nano,
            license_fee_nano=(attributed_media_spend_nano + attributed_data_spend_nano) * budget2.credit.license_fee,
            margin_nano=0,
        )

        effective_spend = daily_statements._get_effective_spend(None, [date], total_spend)
        pct_actual_spend, pct_license_fee, pct_margin = effective_spend[date][campaign]

        self.assertEqual(Decimal('1'), pct_actual_spend)
        self.assertEqual(Decimal('0.6'), pct_license_fee)

    def test_spend_missing(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        budget = dash.models.BudgetLineItem.objects.get(id=1)
        date = datetime.date(2015, 2, 1)

        campaign_spend = {
            'media_nano': 0,
            'data_nano': 0,
        }
        total_spend = {
            date: {
                campaign.id: campaign_spend,
            },
        }

        dash.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=date,
            media_spend_nano=40000000000,
            data_spend_nano=40000000000,
            license_fee_nano=16000000000,
            margin_nano=0,
        )

        effective_spend = daily_statements._get_effective_spend(None, [date], total_spend)
        pct_actual_spend, pct_license_fee, pct_margin = effective_spend[date][campaign]

        self.assertEqual(Decimal('0'), pct_actual_spend)
        self.assertEqual(Decimal('0.2'), pct_license_fee)

    def test_budgets_missing(self):
        campaign = dash.models.Campaign.objects.get(id=1)
        date = datetime.date(2015, 2, 1)

        campaign_spend = {
            'media_nano': 0,
            'data_nano': 0,
        }
        total_spend = {
            date: {
                campaign.id: campaign_spend,
            },
        }

        effective_spend = daily_statements._get_effective_spend(None, [date], total_spend)
        pct_actual_spend, pct_license_fee, pct_margin = effective_spend[date][campaign]

        self.assertEqual(Decimal('0'), pct_actual_spend)
        self.assertEqual(Decimal('0'), pct_license_fee)


@patch('etl.daily_statements_k1._query_ad_groups_with_spend', return_value=[2, 3])
@patch('utils.dates_helper.local_today', return_value=datetime.date(2016, 11, 15))
class GetCampaignsWithSpendTest(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def test_get_campaigns_with_spend(self, mock_local_today, mock_ad_groups):
        since = datetime.date(2016, 11, 1)
        campaigns = daily_statements.get_campaigns_with_spend(since)

        self.assertEqual(campaigns, test_helper.QuerySetMatcher(dash.models.Campaign.objects.filter(pk__in=[1, 2])))
        mock_ad_groups.assert_called_with({
            'tzhour_from': 5,
            'tzhour_to': 5,
            'tzdate_from': '2016-11-12',
            'tzdate_to': '2016-11-16',
            'date_from': '2016-11-12',
            'date_to': '2016-11-15',
        })

    def test_get_campaigns_with_spend_close(self, mock_local_today, mock_ad_groups):
        since = datetime.date(2016, 11, 13)
        campaigns = daily_statements.get_campaigns_with_spend(since)

        self.assertEqual(campaigns, test_helper.QuerySetMatcher(dash.models.Campaign.objects.filter(pk__in=[1, 2])))
        mock_ad_groups.assert_called_with({
            'tzhour_from': 5,
            'tzhour_to': 5,
            'tzdate_from': '2016-11-13',  # use date_since as its later
            'tzdate_to': '2016-11-16',
            'date_from': '2016-11-13',
            'date_to': '2016-11-15',
        })
