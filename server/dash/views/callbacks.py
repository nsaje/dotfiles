import logging
import json

from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from dash.features import contentupload
from utils import request_signer

logger = logging.getLogger(__name__)


@csrf_exempt
def content_upload(request):
    try:
        request_signer.verify_wsgi_request(request, settings.LAMBDA_CONTENT_UPLOAD_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception("Invalid signature.")
        raise Http404

    callback_data = json.loads(request.body)
    if callback_data.get("status") != "ok":
        logger.error("Content upload validation failed. data: %s", str(callback_data))
        return JsonResponse({"status": "fail"})
    candidate = callback_data.get("candidate")
    if not candidate:
        logger.error("Content upload validation returned no candidate. data: %s", str(callback_data))
        return JsonResponse({"status": "fail"})
    contentupload.upload.process_callback(candidate)
    return JsonResponse({"status": "ok"})
