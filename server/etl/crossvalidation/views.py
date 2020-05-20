import datetime

import newrelic.agent
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import dash.features.supply_reports.service as service
from utils import request_signer
from utils import zlogging

logger = zlogging.getLogger(__name__)


@csrf_exempt
def crossvalidation(request):
    newrelic.agent.set_background_task(flag=True)

    try:
        request_signer.verify_wsgi_request(request, settings.BIDDER_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception("Invalid crossvalidation signature.")
        return _error_response("Invalid crossvalidation signature.", status=401)

    try:
        start_date = datetime.datetime.strptime(request.GET["start_date"], "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(request.GET["end_date"], "%Y-%m-%d").date()
    except Exception as e:
        logger.exception("Invalid input parameters.")
        return _error_response(str(e), status=400)

    stats = service.get_crossvalidation_stats(start_date, end_date)

    # filter stats without impressions, so we don't have to use pointers in b1 for json decoding
    response_data = {"status": "OK", "data": [_format_stat(stat) for stat in stats if stat[1] is not None]}

    return JsonResponse(response_data)


def _format_stat(stats):
    return {"bidder_slug": stats[0], "impressions": stats[1], "clicks": stats[2], "cost": stats[3]}


def _error_response(error_msg, status=500):
    return JsonResponse({"status": "ERROR", "error": error_msg}, status=status)
