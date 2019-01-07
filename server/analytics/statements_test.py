import mock
from django.test import TestCase

from analytics import statements


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
