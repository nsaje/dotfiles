import backtosql
import datetime
import mock

from django.test import TestCase, override_settings

from .mv_master_publishers import MasterPublishersView


class MasterPublishersViewTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    @mock.patch("redshiftapi.db.get_write_stats_cursor")
    @mock.patch("redshiftapi.db.get_write_stats_transaction")
    @mock.patch("utils.s3helpers.S3Helper")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        date_from = datetime.date(2016, 7, 1)
        date_to = datetime.date(2016, 7, 3)

        spark_session = mock.MagicMock()
        mv = MasterPublishersView("asd", date_from, date_to, account_id=None, spark_session=spark_session)

        mv.generate()

        self.assertEqual(spark_session.run_file.call_count, 7)
        spark_session.run_file.assert_has_calls(
            [
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/outbrainpublisherstats/*.gz",
                    schema=mock.ANY,
                    table="outbrainpublisherstats",
                ),
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/postclickstats/*.gz",
                    schema=mock.ANY,
                    table="postclickstats",
                ),
                mock.call("sql_to_table.py.tmpl", sql=mock.ANY, table="mv_master_pubs_outbrain"),
                mock.call("sql_to_table.py.tmpl", sql=mock.ANY, table="mv_master_pubs"),
                mock.call(
                    "union_tables.py.tmpl",
                    source_table_1="mv_master_pubs",
                    source_table_2="mv_master_pubs_outbrain",
                    table="mv_master_pubs",
                ),
                mock.call("cache_table.py.tmpl", table="mv_master_pubs"),
                mock.call(
                    "export_table_to_json_s3.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mv_master_pubs/",
                    table="mv_master_pubs",
                ),
            ]
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
                    UNLOAD
                        ('SELECT * FROM outbrainpublisherstats WHERE (date BETWEEN \\'2016-07-01\\' AND \\'2016-07-03\\') ')
                    TO %(s3_url)s
                    DELIMITER AS %(delimiter)s
                    CREDENTIALS %(credentials)s
                    ESCAPE NULL AS '$NA$'
                    GZIP
                    MANIFEST;
                    """
                    ),
                    {
                        "s3_url": "s3://test_bucket/spark/asd/outbrainpublisherstats/outbrainpublisherstats-2016-07-01-2016-07-03-0",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                    UNLOAD
                        ('SELECT * FROM postclickstats WHERE (date BETWEEN \\'2016-07-01\\' AND \\'2016-07-03\\') ')
                    TO %(s3_url)s
                    DELIMITER AS %(delimiter)s
                    CREDENTIALS %(credentials)s
                    ESCAPE NULL AS '$NA$'
                    GZIP
                    MANIFEST;
                    """
                    ),
                    {
                        "s3_url": "s3://test_bucket/spark/asd/postclickstats/postclickstats-2016-07-01-2016-07-03-0",
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "delimiter": "\t",
                    },
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        "DELETE FROM mv_master_pubs WHERE (date BETWEEN %(date_from)s AND %(date_to)s);"
                    ),
                    {"date_from": datetime.date(2016, 7, 1), "date_to": datetime.date(2016, 7, 3)},
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
                COPY mv_master_pubs
                FROM %(s3_url)s
                FORMAT JSON 'auto'
                CREDENTIALS %(credentials)s
                MAXERROR 0
                GZIP;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/spark/asd/mv_master_pubs/",
                        "delimiter": "\t",
                    },
                ),
            ]
        )
