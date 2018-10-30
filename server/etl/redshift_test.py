import datetime

import mock
from django.test import TestCase
from django.test import override_settings

import backtosql
from etl import constants
from etl import redshift


class ReplicasTest(TestCase, backtosql.TestSQLMixin):
    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_prepare_unload_query(self):
        from_date = datetime.date(2016, 5, 1)
        to_date = datetime.date(2016, 5, 3)
        sql, params = redshift.prepare_unload_csv_query("mypath/", "mv_master", from_date, to_date)

        self.assertSQLEquals(
            sql,
            """
        UNLOAD
        ('SELECT * FROM mv_master WHERE (date BETWEEN \\'2016-05-01\\' AND \\'2016-05-03\\') ')
        TO %(s3_url)s
        DELIMITER AS %(delimiter)s
        CREDENTIALS %(credentials)s
        ESCAPE
        NULL AS '$NA$'
        GZIP
        MANIFEST
        ;
        """,
        )

        self.assertDictEqual(
            params,
            {
                "s3_url": "s3://test_bucket/mypath/",
                "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                "delimiter": constants.CSV_DELIMITER,
            },
        )

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_prepare_unload_query_account(self):
        from_date = datetime.date(2016, 5, 1)
        to_date = datetime.date(2016, 5, 3)
        sql, params = redshift.prepare_unload_csv_query("mypath/", "mv_master", from_date, to_date, account_id=16)

        self.assertSQLEquals(
            sql,
            """
        UNLOAD
        ('SELECT * FROM mv_master WHERE (date BETWEEN \\'2016-05-01\\' AND \\'2016-05-03\\') AND account_id = 16')
        TO %(s3_url)s
        DELIMITER AS %(delimiter)s
        CREDENTIALS %(credentials)s
        ESCAPE
        NULL AS '$NA$'
        GZIP
        MANIFEST
        ;
        """,
        )

    @mock.patch("redshiftapi.db.get_write_stats_cursor", autospec=True)
    @mock.patch.object(redshift, "prepare_unload_csv_query", autospec=True)
    def test_unload_table(self, mock_prepare_query, mock_cursor):
        mock_prepare_query.return_value = "", {}
        from_date = datetime.date(2016, 5, 1)
        to_date = datetime.date(2016, 5, 3)
        redshift.unload_table("jobid", "mytable", from_date, to_date, account_id=16)
        mock_prepare_query.assert_called_with(
            "materialized_views_replication/jobid/mytable/mytable-2016-05-01-2016-05-03-16",
            "mytable",
            from_date,
            to_date,
            16,
        )

    @mock.patch("redshiftapi.db.get_write_stats_transaction", autospec=True)
    @mock.patch("redshiftapi.db.get_write_stats_cursor", autospec=True)
    @mock.patch.object(redshift, "prepare_copy_query", autospec=True)
    @mock.patch.object(redshift, "prepare_date_range_delete_query", autospec=True)
    def test_update_table_from_s3(self, mock_prepare_delete, mock_prepare_copy, mock_cursor, mock_transaction):
        mock_prepare_copy.return_value = "", {}
        mock_prepare_delete.return_value = "", {}
        mock_cursor.return_value = mock.MagicMock()
        mock_transaction.return_value = mock.MagicMock()
        from_date = datetime.date(2016, 5, 1)
        to_date = datetime.date(2016, 5, 3)
        redshift.update_table_from_s3("mydb", "s3://mypath/", "mytable", from_date, to_date, account_id=16)
        mock_transaction.assert_called_with("mydb")
        mock_cursor.assert_called_with("mydb")
