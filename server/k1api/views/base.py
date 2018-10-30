import logging
import time

import influx
from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions
from rest_framework.views import APIView

from utils import influx_helper
from utils.rest_common import authentication

logger = logging.getLogger(__name__)


class K1APIView(APIView):
    authentication_classes = (
        authentication.gen_service_authentication("b1", settings.BIDDER_API_SIGN_KEY),
        authentication.gen_service_authentication("k1", settings.K1_API_SIGN_KEY),
        authentication.gen_oauth_authentication("sspd"),
    )
    permission_classes = (permissions.IsAuthenticated,)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        start_time = time.time()
        response = super(K1APIView, self).dispatch(request, *args, **kwargs)
        influx.timing(
            "k1api.request",
            (time.time() - start_time),
            endpoint=self.__class__.__name__,
            path=influx_helper.clean_path(request.path),
            method=request.method,
            status=str(response.status_code),
        )
        return response

    @staticmethod
    def response_ok(content):
        return JsonResponse({"error": None, "response": content})

    @staticmethod
    def response_error(msg, status=400):
        return JsonResponse({"error": msg, "response": None}, status=status)
