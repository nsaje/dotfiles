import time

import djangorestframework_camel_case.util
import ipware.ip
import rest_framework.renderers
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin

import utils.rest_common.authentication
from swinfra import metrics
from utils import influx_helper
from utils import json_helper
from utils import metrics_compat
from utils import zlogging

logger = zlogging.getLogger(__name__)
# fmt: off
REQUEST_TIMER = metrics.new_histogram(
    "restapi_request_histogram",
    labelnames=("endpoint", "path", "method", "status", "user"),
    buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, 20.0, 30.0, 40.0, 50.0, float("inf")),
)
# fmt: on


class RESTAPIJSONRenderer(rest_framework.renderers.JSONRenderer):
    encoder_class = json_helper.JSONEncoder

    def render(self, data, *args, **kwargs):
        return super(RESTAPIJSONRenderer, self).render(
            djangorestframework_camel_case.util.camelize(data), *args, **kwargs
        )


class CanUseRESTAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_use_restapi"))


class RESTAPIBaseView(APIView):
    authentication_classes = [
        utils.rest_common.authentication.OAuth2Authentication,
        utils.rest_common.authentication.SessionAuthentication,
    ]

    renderer_classes = [RESTAPIJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = (permissions.IsAuthenticated, CanUseRESTAPIPermission)

    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    def initialize_request(self, request, *args, **kwargs):
        drf_request = super(RESTAPIBaseView, self).initialize_request(request, *args, **kwargs)
        drf_request.method = request.method
        drf_request.start_time = time.time()
        return drf_request

    def finalize_response(self, request, response, *args, **kwargs):
        drf_response = super(RESTAPIBaseView, self).finalize_response(request, response, *args, **kwargs)
        user = getattr(request, "user", None)
        user_email = getattr(user, "email", "unknown")
        metrics_compat.timing(
            "restapi.request",
            (time.time() - request.start_time),
            endpoint=self.__class__.__name__,
            method=request.method,
            status=str(response.status_code),
            user=user_email,
        )
        REQUEST_TIMER.labels(
            endpoint=self.__class__.__name__,
            path=influx_helper.clean_path(request.path),
            method=request.method,
            status=str(response.status_code),
            user=user_email,
        ).observe(time.time() - request.start_time)
        logger.debug(
            "REST API request/response: endpoint={endpoint}, method={method}, status={status}, user={user}, ip={ip}".format(
                endpoint=self.__class__.__name__,
                method=request.method,
                status=str(response.status_code),
                user=user_email,
                ip=ipware.ip.get_ip(request),
            )
        )
        return drf_response

    @staticmethod
    def response_ok(data, extra=None, errors=None, **kwargs):
        data = {"data": data}
        if extra:
            data["extra"] = extra
        if errors:
            data["errors"] = errors
        return Response(data, **kwargs)

    def perform_authentication(self, request):
        super(RESTAPIBaseView, self).perform_authentication(request)
        if not isinstance(request.successful_authenticator, utils.rest_common.authentication.SessionAuthentication):
            request.is_api_request = True
        else:
            request.is_api_request = False


class RESTAPIBaseViewSet(ViewSetMixin, RESTAPIBaseView):
    pass
