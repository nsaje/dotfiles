import backtosql
import datetime
import mock
import textwrap

from django.test import TestCase, override_settings

from dash import models

from .mv_helpers_campaign_factors import MVHelpersCampaignFactors


@mock.patch("utils.s3helpers.S3Helper")
class MVHCampaignFactorsTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate(self, mock_s3helper):
        spark_session = mock.MagicMock()
        mv = MVHelpersCampaignFactors(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 2), account_id=None, spark_session=spark_session
        )

        mv.generate(
            campaign_factors={
                datetime.date(2016, 7, 1): {
                    models.Campaign.objects.get(pk=1): (1.0, 0.2, 0.25),
                    models.Campaign.objects.get(pk=2): (0.2, 0.2, 0.25),
                },
                datetime.date(2016, 7, 2): {
                    models.Campaign.objects.get(pk=1): (1.0, 0.3, 0.25),
                    models.Campaign.objects.get(pk=2): (0.2, 0.3, 0.25),
                },
            }
        )

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "spark/asd/mvh_campaign_factors/data.csv",
            textwrap.dedent(
                """\
            2016-07-01\t1\t1.0\t0.2\t0.25\r
            2016-07-01\t2\t0.2\t0.2\t0.25\r
            2016-07-02\t1\t1.0\t0.3\t0.25\r
            2016-07-02\t2\t0.2\t0.3\t0.25\r
            """
            ),
        )

        self.assertEqual(spark_session.run_file.call_count, 2)
        spark_session.run_file.assert_has_calls(
            [
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mvh_campaign_factors/data.csv",
                    table="mvh_campaign_factors",
                    schema=mock.ANY,
                ),
                mock.call("cache_table.py.tmpl", table="mvh_campaign_factors"),
            ]
        )

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate_checks_range_continuation(self, mock_s3helper):
        mv = MVHelpersCampaignFactors("asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None)

        with self.assertRaises(Exception):
            mv.generate(
                campaign_factors={
                    datetime.date(2016, 7, 1): {
                        models.Campaign.objects.get(pk=1): (1.0, 0.2, 0.25),
                        models.Campaign.objects.get(pk=2): (0.2, 0.2, 0.25),
                    },
                    # missing for 2016-07-02
                    datetime.date(2016, 7, 3): {
                        models.Campaign.objects.get(pk=1): (1.0, 0.3, 0.25),
                        models.Campaign.objects.get(pk=2): (0.2, 0.3, 0.25),
                    },
                }
            )

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate_account_id(self, mock_s3helper):
        spark_session = mock.MagicMock()
        mv = MVHelpersCampaignFactors(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 2), account_id=1, spark_session=spark_session
        )

        mv.generate(
            campaign_factors={
                datetime.date(2016, 7, 1): {models.Campaign.objects.get(pk=1): (1.0, 0.2, 0.25)},
                datetime.date(2016, 7, 2): {models.Campaign.objects.get(pk=1): (1.0, 0.3, 0.25)},
            }
        )

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "spark/asd/mvh_campaign_factors/data.csv",
            textwrap.dedent(
                """\
            2016-07-01\t1\t1.0\t0.2\t0.25\r
            2016-07-02\t1\t1.0\t0.3\t0.25\r
            """
            ),
        )

        self.assertEqual(spark_session.run_file.call_count, 2)
        spark_session.run_file.assert_has_calls(
            [
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mvh_campaign_factors/data.csv",
                    table="mvh_campaign_factors",
                    schema=mock.ANY,
                ),
                mock.call("cache_table.py.tmpl", table="mvh_campaign_factors"),
            ]
        )
