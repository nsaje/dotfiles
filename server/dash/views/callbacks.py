import logging

from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from utils import request_signer
import dash.upload_plus

logger = logging.getLogger(__name__)


@csrf_exempt
def content_upload(request):
    try:
        request_signer.verify_wsgi_request(request, settings.LAMBDA_CONTENT_UPLOAD_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid signature.')
        raise Http404

    callback_data = request.POST
    if callback_data.get('status') != 'ok':
        logger.warning('Content validation was unsuccessful %s', str(callback_data))
        return JsonResponse({
            'status': 'fail',
        })
    candidate = callback_data.get('candidate')
    if not candidate:
        logger.warning('Content validation returned no candidate %s', str(callback_data))
        return JsonResponse({
            'status': 'fail',
        })
    dash.upload_plus.process_callback(candidate)
    return JsonResponse({
        "status": 'ok'
    })
