import datetime
import textwrap

import mock
from django.test import TestCase
from django.test import override_settings

import backtosql

from .mv_helpers_ad_group_structure import MVHelpersAdGroupStructure


@mock.patch("redshiftapi.db.get_write_stats_cursor")
@mock.patch("redshiftapi.db.get_write_stats_transaction")
@mock.patch("utils.s3helpers.S3Helper")
class MVHAdGroupStructureTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = MVHelpersAdGroupStructure("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_adgroup_structure/2016/07/03/mvh_adgroup_structure_asd.csv",
            textwrap.dedent(
                """\
            1\t1\t1\t1\r
            1\t2\t2\t2\r
            1\t1\t3\t3\r
            1\t1\t1\t4\r
            """
            ),
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
            CREATE TEMP TABLE mvh_adgroup_structure (
                agency_id integer encode lzo,
                account_id integer encode lzo,
                campaign_id integer encode lzo,
                ad_group_id integer encode lzo
            )
            diststyle all
            sortkey(ad_group_id, campaign_id, account_id, agency_id)"""
                    )
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
            COPY mvh_adgroup_structure
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            BLANKSASNULL EMPTYASNULL
            CREDENTIALS %(credentials)s
            MAXERROR 0;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": (
                            "s3://test_bucket/materialized_views/"
                            "mvh_adgroup_structure/2016/07/03/mvh_adgroup_structure_asd.csv"
                        ),
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate_account_id(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = MVHelpersAdGroupStructure("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1)

        mv.generate()

        self.assertTrue(mock_s3helper.called)

        # only account_id=1 is used to generate CSV
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_adgroup_structure/2016/07/03/mvh_adgroup_structure_asd.csv",
            textwrap.dedent(
                """\
            1\t1\t1\t1\r
            1\t1\t3\t3\r
            1\t1\t1\t4\r
            """
            ),
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
            CREATE TEMP TABLE mvh_adgroup_structure (
                agency_id integer encode lzo,
                account_id integer encode lzo,
                campaign_id integer encode lzo,
                ad_group_id integer encode lzo
            )
            diststyle all
            sortkey(ad_group_id, campaign_id, account_id, agency_id)"""
                    )
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
            COPY mvh_adgroup_structure
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            BLANKSASNULL EMPTYASNULL
            CREDENTIALS %(credentials)s
            MAXERROR 0;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": (
                            "s3://test_bucket/materialized_views/"
                            "mvh_adgroup_structure/2016/07/03/mvh_adgroup_structure_asd.csv"
                        ),
                        "delimiter": "\t",
                    },
                ),
            ]
        )
