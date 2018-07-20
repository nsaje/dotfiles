from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from djangorestframework_camel_case.parser import CamelCaseJSONParser


class ServiceAPIBaseView(APIView):
    # override with appropriate utils.rest_common.authentication.gen_service_authentication(...)
    authentication_classes = []

    renderer_classes = [CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def response_ok(data, errors=None, **kwargs):
        data = {"data": data}
        if errors:
            data["errors"] = errors
        return Response(data, **kwargs)
