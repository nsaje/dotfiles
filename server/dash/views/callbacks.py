import logging

from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from utils import request_signer

logger = logging.getLogger(__name__)


@csrf_exempt
def content_upload(request):
    try:
        request_signer.verify_wsgi_request(request, settings.LAMBDA_CONTENT_UPLOAD_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid signature.')
        raise Http404

    # TODO: mark processed candidates

    return JsonResponse({
        "status": 'ok'
    })
