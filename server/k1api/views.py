import json
import logging

from django.views.decorators.csrf import csrf_exempt
import dash.models
from django.http import JsonResponse, Http404
from django.db.models import F
from django.conf import settings

from utils import request_signer

logger = logging.getLogger(__name__)


def _response_ok(content):
    return JsonResponse({
        "error": None,
        "response": content,
    })


def _response_error(msg, status=400):
    return JsonResponse({
        "error": msg,
        "response": None,
    }, status=status)


@csrf_exempt
def get_content_ad_list(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    source_types = request.GET.getlist('source_type')

    ad_groups = (
        dash.models.AdGroup.objects
            .exclude_archived()
            .values(
                'id',
            )
    )
    if source_types:
        ad_groups = ad_groups.filter(
            source__source_type__type__in=source_types)

    return _response_ok(list(ad_groups))


@csrf_exempt
def get_ad_group_list(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    source_types = request.GET.getlist('source_type')

    ad_groups = (
        dash.models.AdGroup.objects
            .exclude_archived()
            .values(
                'id',
            )
    )
    if source_types:
        ad_groups = ad_groups.filter(
            source__source_type__type__in=source_types)

    return _response_ok(list(ad_groups))


@csrf_exempt
def get_ad_group(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    ad_group_id = request.GET.get('ad_group')
    if not ad_group_id:
        return JsonResponse({
            "error": "Must provide ad group id."
        }, status=400)
    source_types = request.GET.getlist('source_type')

    ad_group_sources = (
        dash.models.AdGroupSource.objects
            .filter(ad_group_id=ad_group_id)
            .values(
                'id',
                'ad_group_id',
                'source_credentials_id',
                'source__name',
                'source_campaign_key',
            )
    )
    if source_types:
        ad_group_sources = ad_group_sources.filter(
            source__source_type__type__in=source_types)

    return _response_ok({'ad_group_sources': list(ad_group_sources)})


@csrf_exempt
def get_accounts(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    accounts_list = (
        dash.models.Account.objects
            .all()
            .exclude_archived()
            .values(
                'id',
                'outbrain_marketer_id',
            )
    )

    # construct response dict
    data = {'accounts': list(accounts_list)}
    return _response_ok(data)


@csrf_exempt
def get_source_credentials_for_reports_sync(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    source_types = request.GET.getlist('source_type')

    source_credentials_list = (
        dash.models.SourceCredentials.objects
        .filter(sync_reports=True)
        .filter(source__source_type__type__in=source_types)
        .annotate(
            source_type=F('source__source_type__type'),
        )
        .values(
            'id',
            'credentials',
            'source_type',
        )
    )

    # construct response dict
    data = {}
    data['source_credentials_list'] = list(source_credentials_list)
    return _response_ok(data)


@csrf_exempt
def get_content_ad_source_mapping(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    source_content_ad_ids = json.loads(request.body)
    if not source_content_ad_ids or not isinstance(source_content_ad_ids, list):
        return JsonResponse({
            "error": "Body must be a list of source content ad ids."
        }, status=400)

    contentadsources = (
        dash.models.ContentAdSource.objects
        .filter(source_content_ad_id__in=source_content_ad_ids)
        .annotate(
            ad_group_id=F('content_ad__ad_group_id'),
            source_name=F('source__name'),
        )
        .values(
            'source_content_ad_id',
            'content_ad_id',
            'ad_group_id',
            'source_name',
        )
    )
    source_types = request.GET.getlist('source_type')
    if source_types:
        contentadsources = contentadsources.filter(source__source_type__type__in=source_types)

    data = {'content_ad_sources': list(contentadsources)}

    return _response_ok(data)


@csrf_exempt
def get_ga_accounts(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    ga_accounts = dash.models.GAAnalyticsAccount.objects.all().values('ga_account_id', 'ga_web_property_id')
    return JsonResponse({'ga_accounts': list(ga_accounts)})
