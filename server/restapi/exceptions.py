import logging

from django.core.exceptions import ObjectDoesNotExist
import rest_framework.views
from rest_framework.response import Response
from rest_framework import serializers

from utils import exc


logger = logging.getLogger(__name__)


def custom_exception_handler(exception, context):
    error_data = {}

    response = _handle_client_api_exceptions(exception, context)
    if response:
        return response

    response = _handle_django_rest_framework_exceptions(exception, context)
    if response:
        return response

    # Django DoesNotExist
    if isinstance(exception, ObjectDoesNotExist):
        error_data['errorCode'] = "DoesNotExist"
        error_data['details'] = exception.message
        status_code = 400
        return Response(error_data, status=status_code)

    # Server Error
    logger.error('REST API exception', exc_info=True)
    error_data['errorCode'] = "ServerError"
    error_data['details'] = "An error occurred."
    status_code = 500
    return Response(error_data, status=status_code)


def _handle_client_api_exceptions(exception, context):
    error_data = {}

    if type(exception) in exc.custom_errors:
        error_data["errorCode"] = exception.error_code
        error_data["details"] = exception.pretty_message or exception.message

        if isinstance(exception, exc.ValidationError):
            if exception.errors:
                error_data['details'] = exception.errors
            if exception.data:
                error_data['data'] = exception.data

        status_code = exception.http_status_code
        return Response(error_data, status=status_code)


def _handle_django_rest_framework_exceptions(exception, context):
    error_data = {}
    response = rest_framework.views.exception_handler(exception, context)
    if response:
        error_data['errorCode'] = exception.__class__.__name__
        if isinstance(exception, serializers.ValidationError):
            error_data['details'] = response.data
        else:
            error_data['details'] = response.data.get('detail') or response.data
        response.data = error_data
        return response
