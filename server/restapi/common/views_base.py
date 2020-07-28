import re
from collections import OrderedDict

import rest_framework.renderers
from django.utils.decorators import classonlymethod
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin

import utils.rest_common.authentication
from utils import json_helper
from utils import zlogging

logger = zlogging.getLogger(__name__)


def camelize(data):
    if isinstance(data, dict):
        new_dict = OrderedDict()
        for key, value in data.items():
            new_key = (
                re.sub(r"[a-z]_[a-z]", lambda match: match.group()[0] + match.group()[2].upper(), key)
                if isinstance(key, str)
                else key
            )
            new_dict[new_key] = camelize(value)
        return new_dict
    if isinstance(data, (list, tuple)):
        for i in range(len(data)):
            data[i] = camelize(data[i])
        return data
    return data


class RESTAPIJSONRenderer(rest_framework.renderers.JSONRenderer):
    encoder_class = json_helper.JSONEncoder

    def render(self, data, *args, **kwargs):
        return super(RESTAPIJSONRenderer, self).render(camelize(data), *args, **kwargs)


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

    def dispatch(self, request, *args, **kwargs):
        request.handler_class_name = self.__class__.__name__
        return super(RESTAPIBaseView, self).dispatch(request, *args, **kwargs)

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
    always_allowed_methods = ["trace", "options", "head"]
    """
    as_view is overridden and "http_method_not_allowed" assigned as default value to prevent unsupported/invalid methods
    being called on url endpoints. Exception for trace, options and head.
    """

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        if actions:
            actions = {
                method: actions.get(method, "http_method_not_allowed")
                for method in cls.http_method_names
                if method not in cls.always_allowed_methods
            }
        return super().as_view(actions, **initkwargs)
