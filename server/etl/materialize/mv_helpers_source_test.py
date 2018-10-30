import datetime
import textwrap

import mock
from django.test import TestCase
from django.test import override_settings

import backtosql

from .mv_helpers_source import MVHelpersSource


@mock.patch("redshiftapi.db.get_write_stats_cursor")
@mock.patch("redshiftapi.db.get_write_stats_transaction")
@mock.patch("utils.s3helpers.S3Helper")
class MVHSourceTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = MVHelpersSource("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_source/2016/07/03/mvh_source_asd.csv",
            textwrap.dedent(
                """\
            1\tadblade\tadblade\r
            2\tadiant\tadiant\r
            3\toutbrain\toutbrain\r
            4\tyahoo\tyahoo\r
            """
            ),
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
            CREATE TEMP TABLE mvh_source (
                source_id int2 encode bytedict,
                bidder_slug varchar(127) encode lzo,
                clean_slug varchar(127) encode lzo
            ) sortkey(bidder_slug);"""
                    )
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
            COPY mvh_source
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            BLANKSASNULL EMPTYASNULL
            CREDENTIALS %(credentials)s
            MAXERROR 0;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mvh_source/2016/07/03/mvh_source_asd.csv",
                        "delimiter": "\t",
                    },
                ),
            ]
        )
