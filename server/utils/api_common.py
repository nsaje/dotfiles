import json
import time

from django.conf import settings
from django.http import Http404
from django.http import HttpResponse
from django.views.generic import View

from swinfra import metrics
from utils import influx_helper
from utils import json_helper
from utils import zlogging

from . import exc

logger = zlogging.getLogger(__name__)

# fmt: off
REQUEST_TIMER = metrics.new_histogram(
    "dash_request",
    labelnames=("endpoint", "path", "method", "status"),
    buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, 20.0, 30.0, 40.0, 50.0, float("inf")),
)
# fmt: on


class BaseApiView(View):
    rest_proxy = False

    def __init__(self, rest_proxy=False, *args, **kwargs):
        self.rest_proxy = rest_proxy
        super(BaseApiView, self).__init__(*args, **kwargs)

    def log_error(self, request):
        logger.exception(
            "API exception", extra={"data": {"path": request.path, "GET": request.GET, "POST": dict(request.POST)}}
        )

    def _set_default_reponse_headers(self, response):
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"

    def create_api_response(
        self, data=None, success=True, status_code=200, convert_datetimes_tz=settings.DEFAULT_TIME_ZONE
    ):

        body = {"success": success}

        if data:
            body["data"] = data

        if self.rest_proxy:
            return body, status_code

        response = HttpResponse(
            content=json.dumps(body, cls=json_helper.JSONEncoder, convert_datetimes_tz=convert_datetimes_tz),
            content_type="application/json",
            status=status_code,
        )
        self._set_default_reponse_headers(response)
        return response

    def create_file_response(self, content_type, filename, status_code=200, content=""):
        response = HttpResponse(content, content_type=content_type, status=status_code)
        self._set_default_reponse_headers(response)
        response["Content-Disposition"] = 'attachment; filename="%s"' % filename

        return response

    def create_excel_response(self, filename, status_code=200, content=""):
        return self.create_file_response(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "%s.xlsx" % filename,
            status_code,
            content,
        )

    def create_csv_response(self, filename, status_code=200, content=""):
        return self.create_file_response(
            'text/csv; name="%s.csv"' % filename, "%s.csv" % filename, status_code, content
        )

    def get_exception_response(self, request, exception):
        error_data = {}
        if any(isinstance(exception, custom_error_cls) for custom_error_cls in exc.custom_errors):
            error_data["error_code"] = exception.error_code
            error_data["message"] = exception.pretty_message or exception.args[0]

            if isinstance(exception, exc.ValidationError):
                error_data["errors"] = exception.errors
                error_data["data"] = exception.data

            status_code = exception.http_status_code
        else:
            self.log_error(request)

            error_data["error_code"] = "ServerError"
            error_data["message"] = "An error occurred."

            status_code = 500

        return self.create_api_response(error_data, success=False, status_code=status_code)

    def dispatch(self, request, *args, **kwargs):
        start_time = time.time()
        status = None
        try:
            response = super(BaseApiView, self).dispatch(request, *args, **kwargs)
            status = response.status_code
            return response
        except Http404:
            status = 404
            raise  # django's default 404, will use template found in templates/404.html
        except Exception as e:
            response = self.get_exception_response(request, e)
            status = response.status_code
            return response
        finally:
            REQUEST_TIMER.labels(
                endpoint=self.__class__.__name__,
                path=influx_helper.clean_path(request.path),
                method=request.method,
                status=str(status),
            ).observe(time.time() - start_time)
