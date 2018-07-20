from django.test import TestCase
import rest_framework.serializers
import rest_framework.exceptions

from restapi.common.exceptions import custom_exception_handler
from utils import exc


class AddContentAdSources(TestCase):
    def test_client_exception(self):
        exception = exc.MissingDataError("missing something")
        response = custom_exception_handler(exception, None)
        self.assertEqual(response.data, {"errorCode": "MissingDataError", "details": "missing something"})
        self.assertEqual(response.status_code, exception.http_status_code)

    def test_client_validation_exception(self):
        exception = exc.ValidationError(errors="test errors")
        response = custom_exception_handler(exception, None)
        self.assertEqual(response.data, {"errorCode": "ValidationError", "details": "test errors"})
        self.assertEqual(response.status_code, exception.http_status_code)

    def test_drf_exception(self):
        exception = rest_framework.exceptions.AuthenticationFailed("not authenticated")
        response = custom_exception_handler(exception, None)
        self.assertEqual(response.data, {"errorCode": "AuthenticationFailed", "details": "not authenticated"})
        self.assertEqual(response.status_code, exception.status_code)

    def test_drf_validation_exception(self):
        exception = rest_framework.serializers.ValidationError("missing something")
        response = custom_exception_handler(exception, None)
        self.assertEqual(response.data, {"errorCode": "ValidationError", "details": ["missing something"]})
        self.assertEqual(response.status_code, exception.status_code)
