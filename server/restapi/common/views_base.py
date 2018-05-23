import logging
import influx
import ipware.ip
import time

from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin
import rest_framework.renderers
import rest_framework.parsers
from rest_framework.response import Response
from rest_framework import permissions
from djangorestframework_camel_case.parser import CamelCaseJSONParser
import djangorestframework_camel_case.util

from utils import json_helper
import utils.rest_common.authentication

logger = logging.getLogger(__name__)


class RESTAPIJSONRenderer(rest_framework.renderers.JSONRenderer):
    encoder_class = json_helper.JSONEncoder

    def render(self, data, *args, **kwargs):
        return super(RESTAPIJSONRenderer, self).render(
            djangorestframework_camel_case.util.camelize(data), *args, **kwargs
        )


class CanUseRESTAPIPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm('zemauth.can_use_restapi'))


class RESTAPIBaseView(APIView):
    authentication_classes = [
        utils.rest_common.authentication.OAuth2Authentication,
        utils.rest_common.authentication.SessionAuthentication,
    ]

    renderer_classes = [RESTAPIJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = (permissions.IsAuthenticated, CanUseRESTAPIPermission,)

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def initialize_request(self, request, *args, **kwargs):
        drf_request = super(RESTAPIBaseView, self).initialize_request(request, *args, **kwargs)
        drf_request.method = request.method
        drf_request.start_time = time.time()
        return drf_request

    def finalize_response(self, request, response, *args, **kwargs):
        drf_response = super(RESTAPIBaseView, self).finalize_response(request, response, *args, **kwargs)
        user = getattr(request, 'user', None)
        user_email = getattr(user, 'email', 'unknown')
        influx.timing(
            'restapi.request',
            (time.time() - request.start_time),
            endpoint=self.__class__.__name__,
            method=request.method,
            status=str(response.status_code),
            user=user_email
        )
        logger.debug('REST API request/response: endpoint={endpoint}, method={method}, status={status}, user={user}, ip={ip}'.format(
            endpoint=self.__class__.__name__,
            method=request.method,
            status=str(response.status_code),
            user=user_email,
            ip=ipware.ip.get_ip(request)
        ))
        return drf_response

    @staticmethod
    def response_ok(data, errors=None, **kwargs):
        data = {'data': data}
        if errors:
            data['errors'] = errors
        return Response(data, **kwargs)


class RESTAPIBaseViewSet(ViewSetMixin, RESTAPIBaseView):
    pass
