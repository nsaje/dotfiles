import json

from django.conf import settings
from django.http import Http404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from dash.features import contentupload
from utils import request_signer
from utils import zlogging

logger = zlogging.getLogger(__name__)


@csrf_exempt
def content_upload(request):
    try:
        request_signer.verify_wsgi_request(request, settings.LAMBDA_CONTENT_UPLOAD_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception("Invalid signature.")
        raise Http404

    callback_data = json.loads(request.body)
    if callback_data.get("status") != "ok":
        logger.error("Content upload validation failed.", data=str(callback_data))
        return JsonResponse({"status": "fail"})
    candidate = callback_data.get("candidate")
    if not candidate:
        logger.error("Content upload validation returned no candidate.", data=str(callback_data))
        return JsonResponse({"status": "fail"})
    contentupload.upload.process_callback(candidate)
    return JsonResponse({"status": "ok"})
