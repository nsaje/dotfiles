import collections
import backtosql
import datetime
import mock

from django.test import TestCase, override_settings

from .mv_master import MasterView


PostclickstatsResults = collections.namedtuple(
    "Result2",
    [
        "ad_group_id",
        "postclick_source",
        "content_ad_id",
        "source_slug",
        "publisher",
        "bounced_visits",
        "conversions",
        "new_visits",
        "pageviews",
        "total_time_on_site",
        "visits",
        "users",
    ],
)


class MasterViewTest(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    @mock.patch("utils.s3helpers.S3Helper")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        spark_session = mock.MagicMock()
        mv = MasterView("asd", date_from, date_to, account_id=None, spark_session=spark_session)

        mv.generate()

        self.assertEqual(spark_session.run_file.call_count, 1)
        spark_session.run_file.assert_has_calls(
            [
                mock.call(
                    "export_table_to_json_s3.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mv_master/",
                    table="mv_master",
                )
            ]
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher("DELETE FROM mv_master WHERE (date BETWEEN %(date_from)s AND %(date_to)s);"),
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3)},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                COPY mv_master
                FROM %(s3_url)s
                FORMAT JSON 'auto'
                CREDENTIALS %(credentials)s
                MAXERROR 0
                GZIP;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/spark/asd/mv_master/",
                        "delimiter": "\t",
                    },
                ),
            ]
        )


class MasterViewTestByAccountId(TestCase, backtosql.TestSQLMixin):

    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    @mock.patch("utils.s3helpers.S3Helper")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        account_id = 1
        spark_session = mock.MagicMock()
        mv = MasterView("asd", date_from, date_to, account_id=account_id, spark_session=spark_session)

        mv.generate()

        self.assertEqual(spark_session.run_file.call_count, 1)
        spark_session.run_file.assert_has_calls(
            [
                mock.call(
                    "export_table_to_json_s3.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mv_master/",
                    table="mv_master",
                )
            ]
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
                    DELETE
                    FROM mv_master
                    WHERE (date BETWEEN %(date_from)s AND %(date_to)s) AND account_id=%(account_id)s;
                    """
                    ),
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3), "account_id": 1},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                COPY mv_master
                FROM %(s3_url)s
                FORMAT JSON 'auto'
                CREDENTIALS %(credentials)s
                MAXERROR 0
                GZIP;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/spark/asd/mv_master/",
                        "delimiter": "\t",
                    },
                ),
            ]
        )
