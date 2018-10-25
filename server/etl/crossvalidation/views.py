import datetime
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import newrelic.agent

import redshiftapi.api_breakdowns

from utils import request_signer
import dash.models

logger = logging.getLogger(__name__)


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

    sources = dash.models.Source.objects.filter(source_type__type="b1")
    bidder_slugs = {source.id: source.bidder_slug for source in sources}

    stats = redshiftapi.api_breakdowns.query(
        ["content_ad_id", "source_id", "ad_group_id"],
        {"date__gte": start_date, "date__lte": end_date, "source_id": [source.id for source in sources]},
        None,
        None,
        query_all=True,
    )

    # filter stats without impressions, so we don't have to use pointers in b1 for json decoding
    response_data = {
        "status": "OK",
        "data": [_format_stat(stat, bidder_slugs) for stat in stats if stat["impressions"] is not None],
    }

    return JsonResponse(response_data)


def _format_stat(stat, bidder_slugs):
    return {
        "content_ad_id": stat["content_ad_id"],
        "bidder_slug": bidder_slugs[stat["source_id"]],
        "ad_group_id": stat["ad_group_id"],
        "impressions": stat["impressions"],
        "clicks": stat["clicks"],
        "cost": stat["media_cost"],
    }


def _error_response(error_msg, status=500):
    return JsonResponse({"status": "ERROR", "error": error_msg}, status=status)
