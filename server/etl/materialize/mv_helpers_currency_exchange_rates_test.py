import backtosql
import datetime
import mock
import textwrap

from django.test import TestCase, override_settings

from dash import models
from dash import constants

from utils.magic_mixer import magic_mixer

from .mv_helpers_currency_exchange_rates import MVHelpersCurrencyExchangeRates


@mock.patch("utils.s3helpers.S3Helper")
class MVHCurrencyExchangeRatesTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate(self, mock_s3helper):
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

        spark_session = mock.MagicMock()
        mv = MVHelpersCurrencyExchangeRates(
            "asd", datetime.date(2018, 1, 1), datetime.date(2018, 1, 3), account_id=None, spark_session=spark_session
        )

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "spark/asd/mvh_currency_exchange_rates/data.csv",
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

        self.assertEqual(spark_session.run_file.call_count, 2)
        spark_session.run_file.assert_has_calls(
            [
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mvh_currency_exchange_rates/data.csv",
                    table="mvh_currency_exchange_rates",
                    schema=mock.ANY,
                ),
                mock.call("cache_table.py.tmpl", table="mvh_currency_exchange_rates"),
            ]
        )
