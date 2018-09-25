import backtosql
import datetime
import mock

from django.test import TestCase, override_settings

from .mv_touchpoint_conversions import MVTouchpointConversions


@override_settings(S3_BUCKET_STATS="test_bucket")
class MVTouchpointConversionsTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_generate(self, mock_transaction, mock_cursor):
        spark_session = mock.MagicMock()
        mv = MVTouchpointConversions(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None, spark_session=spark_session
        )

        mv.generate()

        self.assertEqual(4, spark_session.run_file.call_count)
        spark_session.run_file.assert_any_call(
            "load_csv_from_s3_to_table.py.tmpl",
            s3_bucket="test_bucket",
            s3_path="spark/asd/conversions/*.gz",
            table="conversions",
            schema=mock.ANY,
        )
        spark_session.run_file.assert_any_call("sql_to_table.py.tmpl", table="mv_touchpointconversions", sql=mock.ANY)
        spark_session.run_file.assert_any_call("cache_table.py.tmpl", table="mv_touchpointconversions"),
        spark_session.run_file.assert_any_call(
            "export_table_to_json_s3.py.tmpl",
            table="mv_touchpointconversions",
            s3_bucket="test_bucket",
            s3_path="spark/asd/mv_touchpointconversions/",
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_touchpointconversions WHERE (date BETWEEN %(date_from)s AND %(date_to)s);"
                    ),
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3)},
                ),
                mock.call(
                    mock.ANY,
                    {
                        "s3_url": "s3://test_bucket/spark/asd/mv_touchpointconversions/",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    def test_generate_account_id(self, mock_transaction, mock_cursor):
        spark_session = mock.MagicMock()
        mv = MVTouchpointConversions(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1, spark_session=spark_session
        )

        mv.generate()

        self.assertEqual(4, spark_session.run_file.call_count)
        spark_session.run_file.assert_any_call(
            "load_csv_from_s3_to_table.py.tmpl",
            s3_bucket="test_bucket",
            s3_path="spark/asd/conversions/*.gz",
            table="conversions",
            schema=mock.ANY,
        )
        spark_session.run_file.assert_any_call("sql_to_table.py.tmpl", table="mv_touchpointconversions", sql=mock.ANY)
        spark_session.run_file.assert_any_call("cache_table.py.tmpl", table="mv_touchpointconversions"),
        spark_session.run_file.assert_any_call(
            "export_table_to_json_s3.py.tmpl",
            table="mv_touchpointconversions",
            s3_bucket="test_bucket",
            s3_path="spark/asd/mv_touchpointconversions/",
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_touchpointconversions WHERE (date BETWEEN %(date_from)s AND %(date_to)s) AND account_id=%(account_id)s;"
                    ),
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3), "account_id": 1},
                ),
                mock.call(
                    mock.ANY,
                    {
                        "s3_url": "s3://test_bucket/spark/asd/mv_touchpointconversions/",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
            ]
        )
