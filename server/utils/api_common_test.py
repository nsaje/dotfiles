import datetime
import json

from django import test
from django import http
import mock

from utils import api_common
from utils import exc


class BaseApiViewTestCase(test.TestCase):
    def test_create_api_response(self):
        data = {
            'test_obj': {
                'id': 100,
                'first_name': 'Something',
                'datetime': datetime.datetime(2014, 1, 10, 18, 0, 0)
            }
        }
        expected_content = {"data": {"test_obj": {"first_name": "Something", "id": 100, "datetime": "2014-01-10T13:00:00"}}, "success": True}

        response = api_common.BaseApiView().create_api_response(data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), expected_content)

        response = api_common.BaseApiView().create_api_response(data, status_code=500)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.content), expected_content)

    def test_create_file_response(self):
        content_type = 'text/csv'
        filename = 'test.csv'

        response = api_common.BaseApiView().create_file_response(content_type, filename)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], content_type)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="%s"' % filename)

        response = api_common.BaseApiView().create_file_response(content_type, filename, 500)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response['Content-Type'], content_type)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="%s"' % filename)

    def test_create_excel_response(self):
        filename = 'test'

        response = api_common.BaseApiView().create_excel_response(filename)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="%s.xlsx"' % filename)

    def test_create_csv_response(self):
        filename = 'test'

        response = api_common.BaseApiView().create_csv_response(filename)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; name="%s.csv"' % filename)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="%s.csv"' % filename)

    @mock.patch('utils.api_common.logger')
    def test_handle_custom_exception(self, logger_mock):
        request = http.HttpRequest()

        error = exc.MissingDataError()
        response = api_common.BaseApiView().get_exception_response(request, error)

        self.assertFalse(logger_mock.error.called)

        expected_content = {"data": {"message": None, "error_code": "MissingDataError"}, "success": False}
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), expected_content)

        error = exc.MissingDataError('Test')
        response = api_common.BaseApiView().get_exception_response(request, error)
        expected_content = {"data": {"message": "Test", "error_code": "MissingDataError"}, "success": False}
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), expected_content)

    @mock.patch('utils.api_common.logger')
    def test_handle_unknown_exception(self, logger_mock):
        request = http.HttpRequest()
        error = Exception()
        response = api_common.BaseApiView().get_exception_response(request, error)

        expected_content = {"data": {"message": "An error occurred.", "error_code": "ServerError"}, "success": False}
        self.assertTrue(logger_mock.error.called)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.content), expected_content)

    @mock.patch('utils.api_common.logger')
    def test_empty_log(self, logger_mock):
        request = http.HttpRequest()

        api_common.BaseApiView().log_error(request)
        logger_mock.error.assert_called_with(
            'API exception',
            exc_info=True,
            extra={
                'data': {
                    'path': request.path,
                    'GET': request.GET,
                    'POST': dict(request.POST),
                }
            }
        )

    @mock.patch('utils.api_common.logger')
    def test_log(self, logger_mock):
        request = http.HttpRequest()
        request.GET = {'test_get': 'test_get_value'}
        request.POST = {'test_post': 'test_post_value'}

        api_common.BaseApiView().log_error(request)
        logger_mock.error.assert_called_with(
            'API exception',
            exc_info=True,
            extra={
                'data': {
                    'path': request.path,
                    'GET': request.GET,
                    'POST': dict(request.POST),
                }
            }
        )
