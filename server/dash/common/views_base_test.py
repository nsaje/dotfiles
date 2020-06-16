import datetime
import json

import mock
from django import http
from django import test

from utils import exc

from .views_base import DASHAPIBaseView


class DASHAPIBaseViewTestCase(test.TestCase):
    def test_create_api_response(self):
        data = {
            "test_obj": {"id": 100, "first_name": "Something", "datetime": datetime.datetime(2014, 1, 10, 18, 0, 0)}
        }
        expected_content = {
            "data": {"test_obj": {"first_name": "Something", "id": 100, "datetime": "2014-01-10T13:00:00"}},
            "success": True,
        }

        response = DASHAPIBaseView().create_api_response(data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), expected_content)

        response = DASHAPIBaseView().create_api_response(data, status_code=500)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.content), expected_content)

    def test_create_file_response(self):
        content_type = "text/csv"
        filename = "test.csv"

        response = DASHAPIBaseView().create_file_response(content_type, filename)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], content_type)
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="%s"' % filename)

        response = DASHAPIBaseView().create_file_response(content_type, filename, 500)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response["Content-Type"], content_type)
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="%s"' % filename)

    def test_create_excel_response(self):
        filename = "test"

        response = DASHAPIBaseView().create_excel_response(filename)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="%s.xlsx"' % filename)

    def test_create_csv_response(self):
        filename = "test"

        response = DASHAPIBaseView().create_csv_response(filename)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], 'text/csv; name="%s.csv"' % filename)
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="%s.csv"' % filename)

    @mock.patch("dash.common.views_base.logger")
    def test_handle_custom_exception(self, logger_mock):
        request = http.HttpRequest()

        error = exc.MissingDataError()
        response = DASHAPIBaseView().get_exception_response(request, error)

        self.assertFalse(logger_mock.error.called)

        expected_content = {"data": {"message": None, "error_code": "MissingDataError"}, "success": False}
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), expected_content)

        error = exc.MissingDataError("Test")
        response = DASHAPIBaseView().get_exception_response(request, error)
        expected_content = {"data": {"message": "Test", "error_code": "MissingDataError"}, "success": False}
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), expected_content)

    @mock.patch("dash.common.views_base.logger")
    def test_handle_custom_exception_subclass(self, logger_mock):
        request = http.HttpRequest()

        class MyCustomError(exc.ValidationError):
            pass

        error = MyCustomError("test")
        response = DASHAPIBaseView().get_exception_response(request, error)

        self.assertFalse(logger_mock.error.called)

        expected_content = {
            "data": {"message": "test", "error_code": "MyCustomError", "errors": None, "data": None},
            "success": False,
        }
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), expected_content)

    @mock.patch("dash.common.views_base.logger")
    def test_handle_unknown_exception(self, logger_mock):
        request = http.HttpRequest()
        error = Exception()
        response = DASHAPIBaseView().get_exception_response(request, error)

        expected_content = {"data": {"message": "An error occurred.", "error_code": "ServerError"}, "success": False}
        self.assertTrue(logger_mock.exception.called)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.content), expected_content)

    @mock.patch("dash.common.views_base.logger")
    def test_empty_log(self, logger_mock):
        request = http.HttpRequest()

        DASHAPIBaseView().log_error(request)
        logger_mock.exception.assert_called_with(
            "API exception", extra={"data": {"path": request.path, "GET": request.GET, "POST": dict(request.POST)}}
        )

    @mock.patch("dash.common.views_base.logger")
    def test_log(self, logger_mock):
        request = http.HttpRequest()
        request.GET = {"test_get": "test_get_value"}
        request.POST = {"test_post": "test_post_value"}

        DASHAPIBaseView().log_error(request)
        logger_mock.exception.assert_called_with(
            "API exception", extra={"data": {"path": request.path, "GET": request.GET, "POST": dict(request.POST)}}
        )
