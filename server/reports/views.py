import datetime
import json
import logging

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from django.conf import settings

import newrelic.agent

from utils import request_signer

import reports.api_contentads
import dash.models

logger = logging.getLogger(__name__)

@csrf_exempt
def crossvalidation(request):
    newrelic.agent.set_background_task(flag=True)

    try:
        request_signer.verify_wsgi_request(request, settings.BIDDER_API_SIGN_KEY)
    except request_signer.SignatureError as e:
        logger.exception('Invalid crossvalidation signature.')
        return _error_response('Invalid crossvalidation signature.', status=401)

    try:
        start_date = datetime.datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
    except Exception as e:
        logger.exception('Invalid input parameters.')
        return _error_response(str(e), status=400)

    sources = dash.models.Source.objects.filter(source_type__type = 'b1')
    bidder_slugs = {source.id: source.bidder_slug for source in sources}

    demo_adgroups = dash.models.AdGroup.objects.filter(is_demo = True)

    stats = reports.api_contentads.query(
        start_date,
        end_date,
        breakdown=['content_ad', 'source', 'ad_group'],
        source__eq = [source.id for source in sources],
        ad_group__neq = [adgroup.id for adgroup in demo_adgroups],
    )

    response_data = {
        'status': 'OK',
        'data': [_format_stat(stat, bidder_slugs) for stat in stats if stat['impressions'] is not None],
    }

    return JsonResponse(response_data)

def _format_stat(stat, bidder_slugs):
    return {
        'content_ad_id': stat['content_ad'],
        'bidder_slug': bidder_slugs[stat['source']],
        'ad_group_id': stat['ad_group'],
        'impressions': stat['impressions'],
        'clicks': stat['clicks'],
        'cost': stat['cost'],
    }

def _error_response(error_msg, status=500):
    return JsonResponse({
        'status': 'ERROR',
        'error': error_msg,
    }, status=status)
