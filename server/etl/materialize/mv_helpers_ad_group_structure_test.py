import backtosql
import datetime
import mock
import textwrap

from django.test import TestCase, override_settings

from .mv_helpers_ad_group_structure import MVHelpersAdGroupStructure


@mock.patch("utils.s3helpers.S3Helper")
class MVHAdGroupStructureTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate(self, mock_s3helper):
        spark_session = mock.MagicMock()
        mv = MVHelpersAdGroupStructure(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None, spark_session=spark_session
        )

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "spark/asd/mvh_adgroup_structure/data.csv",
            textwrap.dedent(
                """\
            1\t1\t1\t1\r
            1\t2\t2\t2\r
            1\t1\t3\t3\r
            1\t1\t1\t4\r
            """
            ),
        )

        self.assertEqual(spark_session.run_file.call_count, 2)
        spark_session.run_file.assert_has_calls(
            [
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mvh_adgroup_structure/data.csv",
                    table="mvh_adgroup_structure",
                    schema=mock.ANY,
                ),
                mock.call("cache_table.py.tmpl", table="mvh_adgroup_structure"),
            ]
        )

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate_account_id(self, mock_s3helper):
        spark_session = mock.MagicMock()
        mv = MVHelpersAdGroupStructure(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=1, spark_session=spark_session
        )

        mv.generate()

        self.assertTrue(mock_s3helper.called)

        # only account_id=1 is used to generate CSV
        mock_s3helper().put.assert_called_with(
            "spark/asd/mvh_adgroup_structure/data.csv",
            textwrap.dedent(
                """\
            1\t1\t1\t1\r
            1\t1\t3\t3\r
            1\t1\t1\t4\r
            """
            ),
        )

        self.assertEqual(spark_session.run_file.call_count, 2)
        spark_session.run_file.assert_has_calls(
            [
                mock.call(
                    "load_csv_from_s3_to_table.py.tmpl",
                    s3_bucket="test_bucket",
                    s3_path="spark/asd/mvh_adgroup_structure/data.csv",
                    table="mvh_adgroup_structure",
                    schema=mock.ANY,
                ),
                mock.call("cache_table.py.tmpl", table="mvh_adgroup_structure"),
            ]
        )
