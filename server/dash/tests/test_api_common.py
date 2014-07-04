import datetime

from django import test
from django import http
import mock

from dash import api_common
from dash import exc


class BaseApiViewTestCase(test.TestCase):
    def test_create_api_response(self):
        data = {
            'test_obj': {
                'id': 100,
                'first_name': 'Something',
                'datetime': datetime.datetime(2014, 1, 10, 18, 0, 0)
            }
        }
        expected_content = '{"data": {"test_obj": {"first_name": "Something", "id": 100, "datetime": "2014-01-10T18:00:00"}}, "success": true}'

        response = api_common.BaseApiView().create_api_response(data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected_content)

        response = api_common.BaseApiView().create_api_response(data, status_code=500)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, expected_content)

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

    @mock.patch('dash.api_common.logger')
    def test_handle_custom_exception(self, logger_mock):
        request = http.HttpRequest()
        request._body = ''

        error = exc.MissingDataError()
        response = api_common.BaseApiView().get_exception_response(request, error)

        self.assertTrue(logger_mock.warning.called)

        expected_content = '{"data": {"message": null, "error_code": "MissingDataError"}, "success": false}'
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, expected_content)

        error = exc.MissingDataError('Test')
        response = api_common.BaseApiView().get_exception_response(request, error)
        expected_content = '{"data": {"message": "Test", "error_code": "MissingDataError"}, "success": false}'
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, expected_content)

    @mock.patch('dash.api_common.logger')
    def test_handle_unknown_exception(self, logger_mock):
        request = http.HttpRequest()
        request._body = ''
        error = Exception()
        response = api_common.BaseApiView().get_exception_response(request, error)

        expected_content = '{"data": {"message": "An error occurred.", "error_code": "ServerError"}, "success": false}'
        self.assertTrue(logger_mock.exception.called)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, expected_content)

    def test_empty_log(self):
        request = http.HttpRequest()
        request._body = ''

        expected_msg = 'GET: []\nPOST: []\nBody: \nArgs:\n\nKwargs:\n'
        self.assertEqual(api_common.BaseApiView().get_log_message(request), expected_msg)

    def test_log(self):
        request = http.HttpRequest()
        request.GET = {'test_get': 'test_get_value'}
        request.POST = {'test_post': 'test_post_value'}
        request._body = 'test'

        expected_msg = "GET: [('test_get', 'test_get_value')]\nPOST: [('test_post', 'test_post_value')]\nBody: test\nArgs:\nTest\nKwargs:\nexc: Test2"

        msg = api_common.BaseApiView().get_log_message(
            request, Exception('Test'), exc=Exception('Test2'))
        self.assertEqual(msg, expected_msg)
