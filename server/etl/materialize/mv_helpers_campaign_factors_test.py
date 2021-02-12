import datetime
import textwrap

import mock
from django.test import TestCase
from django.test import override_settings

import backtosql
from dash import models

from .mv_helpers_campaign_factors import MVHelpersCampaignFactors


@mock.patch("redshiftapi.db.get_write_stats_cursor")
@mock.patch("redshiftapi.db.get_write_stats_transaction")
@mock.patch("utils.s3helpers.S3Helper")
class MVHCampaignFactorsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = MVHelpersCampaignFactors("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 2), account_id=None)

        mv.generate(
            campaign_factors={
                datetime.date(2016, 7, 1): {
                    models.Campaign.objects.get(pk=1): (1.0, 0.1, 0.2, 0.25),
                    models.Campaign.objects.get(pk=2): (0.2, 0.1, 0.2, 0.25),
                },
                datetime.date(2016, 7, 2): {
                    models.Campaign.objects.get(pk=1): (1.0, 0.2, 0.3, 0.25),
                    models.Campaign.objects.get(pk=2): (0.2, 0.2, 0.3, 0.25),
                },
            }
        )

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_campaign_factors/2016/07/02/mvh_campaign_factors_asd.csv",
            textwrap.dedent(
                """\
            2016-07-01\t1\t1.0\t0.1\t0.2\t0.25\r
            2016-07-01\t2\t0.2\t0.1\t0.2\t0.25\r
            2016-07-02\t1\t1.0\t0.2\t0.3\t0.25\r
            2016-07-02\t2\t0.2\t0.2\t0.3\t0.25\r
            """
            ),
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
            CREATE TEMP TABLE mvh_campaign_factors (
                date date not null encode AZ64,
                campaign_id integer not null encode AZ64,

                pct_actual_spend decimal(22, 18) encode AZ64,
                pct_service_fee decimal(22, 18) encode AZ64,
                pct_license_fee decimal(22, 18) encode AZ64,
                pct_margin decimal(22, 18) encode AZ64
            )
            diststyle all
            sortkey(date, campaign_id)"""
                    )
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
            COPY mvh_campaign_factors
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
                            "mvh_campaign_factors/2016/07/02/mvh_campaign_factors_asd.csv"
                        ),
                        "delimiter": "\t",
                    },
                ),
            ]
        )

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate_checks_range_continuation(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = MVHelpersCampaignFactors("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        with self.assertRaises(Exception):
            mv.generate(
                campaign_factors={
                    datetime.date(2016, 7, 1): {
                        models.Campaign.objects.get(pk=1): (1.0, 0.1, 0.2, 0.25),
                        models.Campaign.objects.get(pk=2): (0.2, 0.1, 0.2, 0.25),
                    },
                    # missing for 2016-07-02
                    datetime.date(2016, 7, 3): {
                        models.Campaign.objects.get(pk=1): (1.0, 0.2, 0.3, 0.25),
                        models.Campaign.objects.get(pk=2): (0.2, 0.2, 0.3, 0.25),
                    },
                }
            )

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate_account_id(self, mock_s3helper, mock_transaction, mock_cursor):
        mv = MVHelpersCampaignFactors("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 2), account_id=1)

        mv.generate(
            campaign_factors={
                datetime.date(2016, 7, 1): {models.Campaign.objects.get(pk=1): (1.0, 0.1, 0.2, 0.25)},
                datetime.date(2016, 7, 2): {models.Campaign.objects.get(pk=1): (1.0, 0.2, 0.3, 0.25)},
            }
        )

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "materialized_views/mvh_campaign_factors/2016/07/02/mvh_campaign_factors_asd.csv",
            textwrap.dedent(
                """\
            2016-07-01\t1\t1.0\t0.1\t0.2\t0.25\r
            2016-07-02\t1\t1.0\t0.2\t0.3\t0.25\r
            """
            ),
        )

        mock_cursor().__enter__().execute.assert_has_calls(
            [
                mock.call(
                    backtosql.SQLMatcher(
                        """
            CREATE TEMP TABLE mvh_campaign_factors (
                date date not null encode AZ64,
                campaign_id integer not null encode AZ64,

                pct_actual_spend decimal(22, 18) encode AZ64,
                pct_service_fee decimal(22, 18) encode AZ64,
                pct_license_fee decimal(22, 18) encode AZ64,
                pct_margin decimal(22, 18) encode AZ64
            )
            diststyle all
            sortkey(date, campaign_id)"""
                    )
                ),
                mock.call(
                    backtosql.SQLMatcher(
                        """
            COPY mvh_campaign_factors
            FROM %(s3_url)s
            FORMAT CSV
            DELIMITER AS %(delimiter)s
            BLANKSASNULL EMPTYASNULL
            CREDENTIALS %(credentials)s
            MAXERROR 0;"""
                    ),
                    {
                        "credentials": "aws_access_key_id=bar;aws_secret_access_key=foo",
                        "s3_url": "s3://test_bucket/materialized_views/mvh_campaign_factors/2016/07/02/mvh_campaign_factors_asd.csv",
                        "delimiter": "\t",
                    },
                ),
            ]
        )
