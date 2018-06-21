import logging
import time

import influx
from django.conf import settings
from django.http import JsonResponse, Http404
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from utils import request_signer
from utils import influx_helper

logger = logging.getLogger(__name__)


class K1APIView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self._validate_signature(request)
        start_time = time.time()
        response = super(K1APIView, self).dispatch(request, *args, **kwargs)
        influx.timing(
            'k1api.request',
            (time.time() - start_time),
            endpoint=self.__class__.__name__,
            path=influx_helper.clean_path(request.path),
            method=request.method,
            status=str(response.status_code),
        )
        return response

    @staticmethod
    def _validate_signature(request):
        try:
            request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY + settings.BIDDER_API_SIGN_KEY)
        except request_signer.SignatureError:
            logger.exception('Invalid K1 signature.')
            raise Http404

    @staticmethod
    def response_ok(content):
        return JsonResponse({
            "error": None,
            "response": content,
        })

    @staticmethod
    def response_error(msg, status=400):
        return JsonResponse({
            "error": msg,
            "response": None,
        }, status=status)
