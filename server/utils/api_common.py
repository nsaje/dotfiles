import json
import logging

from django.http import HttpResponse
from django.views.generic import View

from utils import json_helper
import exc

logger = logging.getLogger(__name__)


class BaseApiView(View):
    def get_log_message(self, request, *args, **kwargs):
        msg = 'GET: {0}\nPOST: {1}\nBody: {2}\nArgs:\n{3}\nKwargs:\n{4}'.format(
            str(request.GET.items()),
            str(request.POST.items()),
            str(request.body),
            '\n'.join(str(x) for x in args),
            '\n'.join('{0}: {1}'.format(k, str(v)) for k, v in kwargs.iteritems())
        )

        return msg

    def create_api_response(self, data=None, success=True, status_code=200):
        body = {'success': success}

        if data:
            body['data'] = data

        response = HttpResponse(
            content=json.dumps(body, cls=json_helper.JSONEncoder),
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
        error = {}
        if type(exception) in exc.custom_errors:
            logger.warning(self.get_log_message(request, exception))

            error["error_code"] = exception.error_code
            error["message"] = exception.pretty_message or exception.message

            if isinstance(exception, exc.ValidationError):
                error['errors'] = exception.errors

            status_code = exception.http_status_code
        else:
            logger.exception(self.get_log_message(request, exception))

            error["error_code"] = "ServerError"
            error["message"] = "An error occurred."

            status_code = 500

        return self.create_api_response(error, success=False, status_code=status_code)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(BaseApiView, self).dispatch(request, *args, **kwargs)
        except Exception as e:
            return self.get_exception_response(request, e)
