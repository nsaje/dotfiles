import logging

from django.conf import settings
from django.http import JsonResponse, Http404
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from utils import request_signer


logger = logging.getLogger(__name__)


class BizwireView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self._validate_signature(request)
        return super(BizwireView, self).dispatch(request, *args, **kwargs)

    @staticmethod
    def _validate_signature(request):
        try:
            request_signer.verify_wsgi_request(request, settings.BIZWIRE_API_SIGN_KEY)
        except request_signer.SignatureError:
            logger.exception('Invalid signature.')
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


class PromotionExport(BizwireView):
    def get(self, request):
        return self.response_ok({
            "article": {
                "title": "Title comes here",
                "description": "Description comes here"
            },
            "statistics": {
                "headline_impressions": 123,
                "release_views": 123,
                "ctr": 0.01,
                "industry_ctr": 0.01,
                "publishers": [
                    "example.com",
                    "second-example.com",
                    "third-example.com"
                ],
                "geo_headline_impressions": {
                    "US-AL": 1,
                    "US-AK": 2,
                    "US-AZ": 3,
                    "US-AR": 4
                }
            }
        })
