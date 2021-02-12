import datetime
import textwrap

import mock
from django.test import TestCase
from django.test import override_settings

import backtosql
from dash import constants
from dash import models
from utils.magic_mixer import magic_mixer

from .mv_helpers_currency_exchange_rates import MVHelpersCurrencyExchangeRates


@mock.patch("redshiftapi.db.get_write_stats_cursor")
@mock.patch("redshiftapi.db.get_write_stats_transaction")
@mock.patch("utils.s3helpers.S3Helper")
class MVHCurrencyExchangeRatesTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            date=datetime.date(2018, 1, 1),
            currency=constants.Currency.USD,
            exchange_rate=1,
        )
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            date=datetime.date(2018, 1, 1),
            currency=constants.Currency.EUR,
            exchange_rate=1.1,
        )
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            date=datetime.date(2018, 1, 3),
            currency=constants.Currency.EUR,
            exchange_rate=1.2,
        )

        mv = MVHelpersCurrencyExchangeRates(
            "asd", datetime.date(2018, 1, 1), datetime.date(2018, 1, 3), account_id=None
        )

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_currency_exchange_rates/2018/01/03/mvh_currency_exchange_rates_asd.csv",
            textwrap.dedent(
                """\
            2018-01-01\t1\t1.0000\r
            2018-01-02\t1\t1.0000\r
            2018-01-03\t1\t1.0000\r
            2018-01-01\t2\t1.1000\r
            2018-01-02\t2\t1.1000\r
            2018-01-03\t2\t1.2000\r
            """
            ),
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
            CREATE TEMP TABLE mvh_currency_exchange_rates (
                date date not null encode AZ64,
                account_id integer not null encode AZ64,
                exchange_rate decimal(10, 4) encode AZ64
            )
            diststyle all
            sortkey(date, account_id)"""
                    )
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
            COPY mvh_currency_exchange_rates
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            BLANKSASNULL EMPTYASNULL
            CREDENTIALS %(credentials)s
            MAXERROR 0;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mvh_currency_exchange_rates/2018/01/03/mvh_currency_exchange_rates_asd.csv",
                        "delimiter": "\t",
                    },
                ),
            ]
        )
