import mock

from django.test import TestCase

from analytics import statements
import dash.models


class TestStatements(TestCase):
    fixtures = ["test_api"]

    @mock.patch.object(statements.s3helpers.S3Helper, "put")
    @mock.patch.object(statements.s3helpers.S3Helper, "__init__", lambda *args: None)
    def test_generate_csv(self, s3_mock):
        self.assertEqual(
            statements.generate_csv("path/file.csv", lambda: "csv-content"),
            "https://one.zemanta.com/api/custom_report_download/?path=path%2Ffile.csv",
        )
        s3_mock.assert_called_with("path/file.csv", "csv-content", human_readable_filename="file.csv")

    def test_get_url(self):
        self.assertEqual(statements.get_url("test"), "https://one.zemanta.com/api/custom_report_download/?path=test")
        self.assertEqual(
            statements.get_url("test test"), "https://one.zemanta.com/api/custom_report_download/?path=test+test"
        )
        self.assertEqual(
            statements.get_url("test/test.csv"),
            "https://one.zemanta.com/api/custom_report_download/?path=test%2Ftest.csv",
        )

    @mock.patch("redshiftapi.db.get_stats_cursor")
    def test_get_inventory_report(self, mock_cursor):
        cur = mock.MagicMock(name="cursor")
        cur.fetchall = mock.MagicMock(return_value=[("yahoo", "US", 2, 10), ("yahoo", "DE", 2, 10)])
        get_cursor = mock.Mock()
        get_cursor.__exit__ = mock.MagicMock(return_value=False)
        get_cursor.__enter__ = mock.MagicMock(return_value=cur)
        mock_cursor.return_value = get_cursor

        for source in dash.models.Source.objects.all():
            if not source.bidder_slug:
                source.bidder_slug = source.tracking_slug
                source.save()

        yahoo = dash.models.Source.objects.get(pk=5)
        self.assertEqual(
            statements.get_inventory_report(),
            [(yahoo, "US", "PC", 10, 0.3333333333333333), (yahoo, "DE", "PC", 10, 0.3333333333333333)],
        )
