import backtosql
import datetime
import mock

from django.test import TestCase, override_settings

import dash.constants
from utils import test_helper

from .mv_helpers_normalized_stats import MVHelpersNormalizedStats


@mock.patch("backtosql.generate_sql")
@mock.patch("etl.redshift.unload_table_tz")
@mock.patch("redshiftapi.db.get_write_stats_cursor")
@mock.patch("redshiftapi.db.get_write_stats_transaction")
@override_settings(S3_BUCKET_STATS="test-bucket")
class MVHNormalizedStatsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    def test_generate(self, mock_transaction, mock_cursor, mock_unload, mock_backtosql):
        spark_session = mock.MagicMock()
        mv = MVHelpersNormalizedStats(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None, spark_session=spark_session
        )

        mv.generate()

        mock_unload.assert_called_once_with(
            "asd", "stats", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), prefix="spark", account_id=None
        )
        mock_backtosql.assert_any_call(
            "etl_spark_mvh_clean_stats.sql",
            {
                "account_id": None,
                "yahoo_slug": "yahoo",
                "outbrain_slug": "outbrain",
                "valid_placement_mediums": dash.constants.PlacementMedium.get_all(),
                "tzhour_from": 4,
                "tzhour_to": 4,
                "tzdate_from": "2016-07-01",
                "tzdate_to": "2016-07-04",
                "date_from": "2016-07-01",
                "date_to": "2016-07-03",
                "date_ranges": [
                    {
                        "date": "2016-07-01",
                        "tzdate_from": "2016-07-01",
                        "tzdate_to": "2016-07-02",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-07-02",
                        "tzdate_from": "2016-07-02",
                        "tzdate_to": "2016-07-03",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-07-03",
                        "tzdate_from": "2016-07-03",
                        "tzdate_to": "2016-07-04",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                ],
            },
        )
        spark_session.run_file.assert_called_once_with(
            "mvh_clean_stats.py",
            bucket="test-bucket",
            input_table="stats",
            output_table="mvh_clean_stats",
            prefix="spark",
            sql=mock.ANY,
            job_id="asd",
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(mock.ANY),
                mock.call(
                    mock.ANY,
                    {
                        "s3_url": "s3://test-bucket/spark/asd/mvh_clean_stats",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    def test_generate_account_id(self, mock_transaction, mock_cursor, mock_unload, mock_backtosql):
        spark_session = mock.MagicMock()
        mv = MVHelpersNormalizedStats(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1, spark_session=spark_session
        )

        mv.generate()
        mock_unload.assert_called_once_with(
            "asd", "stats", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), prefix="spark", account_id=1
        )
        mock_backtosql.assert_any_call(
            "etl_spark_mvh_clean_stats.sql",
            {
                "account_id": 1,
                "ad_group_id": test_helper.ListMatcher([1, 3, 4]),
                "yahoo_slug": "yahoo",
                "outbrain_slug": "outbrain",
                "valid_placement_mediums": dash.constants.PlacementMedium.get_all(),
                "tzhour_from": 4,
                "tzhour_to": 4,
                "tzdate_from": "2016-07-01",
                "tzdate_to": "2016-07-04",
                "date_from": "2016-07-01",
                "date_to": "2016-07-03",
                "date_ranges": [
                    {
                        "date": "2016-07-01",
                        "tzdate_from": "2016-07-01",
                        "tzdate_to": "2016-07-02",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-07-02",
                        "tzdate_from": "2016-07-02",
                        "tzdate_to": "2016-07-03",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                    {
                        "date": "2016-07-03",
                        "tzdate_from": "2016-07-03",
                        "tzdate_to": "2016-07-04",
                        "tzhour_from": 4,
                        "tzhour_to": 4,
                    },
                ],
            },
        )
        spark_session.run_file.assert_called_once_with(
            "mvh_clean_stats.py",
            bucket="test-bucket",
            input_table="stats",
            output_table="mvh_clean_stats",
            prefix="spark",
            sql=mock.ANY,
            job_id="asd",
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(mock.ANY),
                mock.call(
                    mock.ANY,
                    {
                        "s3_url": "s3://test-bucket/spark/asd/mvh_clean_stats",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
            ]
        )
