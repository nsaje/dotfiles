from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions
from rest_framework.views import APIView

from utils.rest_common import authentication


class K1APIView(APIView):
    authentication_classes = (
        authentication.gen_service_authentication("b1", settings.BIDDER_API_SIGN_KEY),
        authentication.gen_service_authentication("k1", settings.K1_API_SIGN_KEY),
        authentication.gen_oauth_authentication("sspd"),
    )
    permission_classes = (permissions.IsAuthenticated,)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        request.handler_class_name = self.__class__.__name__
        return super(K1APIView, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def response_ok(content):
        return JsonResponse({"error": None, "response": content})

    @staticmethod
    def response_error(msg, status=400):
        return JsonResponse({"error": msg, "response": None}, status=status)
