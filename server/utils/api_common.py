import json
import logging

from django.http import HttpResponse
from django.views.generic import View
from django.conf import settings

from utils import json_helper
import exc

logger = logging.getLogger(__name__)


class BaseApiView(View):
    def log_error(self, request):
        logger.error('API exception', exc_info=True, extra={
            'data': {
                'path': request.path,
                'GET': request.GET,
                'POST': dict(request.POST),
            }
        })

    def create_api_response(
            self,
            data=None,
            success=True,
            status_code=200,
            convert_datetimes_tz=settings.DEFAULT_TIME_ZONE):

        body = {'success': success}

        if data:
            body['data'] = data

        response = HttpResponse(
            content=json.dumps(
                body,
                cls=json_helper.JSONEncoder,
                convert_datetimes_tz=convert_datetimes_tz
            ),
            content_type='application/json',
            status=status_code
        )

        return response

    def create_file_response(self, content_type, filename, status_code=200, content=''):
        response = HttpResponse(
            content,
            content_type=content_type,
            status=status_code
        )

        response['Content-Disposition'] = 'attachment; filename="%s"' % filename

        return response

    def create_excel_response(self, filename, status_code=200, content=''):
        return self.create_file_response(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '%s.xlsx' % filename,
            status_code,
            content
        )

    def create_csv_response(self, filename, status_code=200, content=''):
        return self.create_file_response(
            'text/csv; name="%s.csv"' % filename,
            '%s.csv' % filename,
            status_code,
            content
        )

    def get_exception_response(self, request, exception):
        error_data = {}
        if type(exception) in exc.custom_errors:
            error_data["error_code"] = exception.error_code
            error_data["message"] = exception.pretty_message or exception.message

            if isinstance(exception, exc.ValidationError):
                error_data['errors'] = exception.errors
                error_data['data'] = exception.data

            status_code = exception.http_status_code
        else:
            self.log_error(request)

            error_data["error_code"] = "ServerError"
            error_data["message"] = "An error occurred."

            status_code = 500

        return self.create_api_response(error_data, success=False, status_code=status_code)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(BaseApiView, self).dispatch(request, *args, **kwargs)
        except Exception as e:
            return self.get_exception_response(request, e)
