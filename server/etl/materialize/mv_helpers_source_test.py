import backtosql
import datetime
import mock
import textwrap

from django.test import TestCase, override_settings

from .mv_helpers_source import MVHelpersSource


@mock.patch("utils.s3helpers.S3Helper")
class MVHSourceTest(TestCase, backtosql.TestSQLMixin):
    fixtures = ["test_materialize_views"]

    @override_settings(S3_BUCKET_STATS="test_bucket")
    def test_generate(self, mock_s3helper):
        spark_session = mock.MagicMock()
        mv = MVHelpersSource(
            "asd", datetime.date(2016, 7, 1), datetime.date(2016, 7, 3), account_id=None, spark_session=spark_session
        )

        mv.generate()

        self.assertTrue(mock_s3helper.called)
        mock_s3helper().put.assert_called_with(
            "spark/asd/mvh_source/data.csv",
            textwrap.dedent(
                """\
            1\tadblade\tadblade\r
            2\tadiant\tadiant\r
            3\toutbrain\toutbrain\r
            4\tyahoo\tyahoo\r
            """
            ),
        )

        spark_session.run_file.assert_called_once_with(
            "load_csv_from_s3_to_table.py.tmpl",
            s3_bucket="test_bucket",
            s3_path="spark/asd/mvh_source/data.csv",
            table="mvh_source",
            schema=mock.ANY,
        )
