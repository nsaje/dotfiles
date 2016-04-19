import json
import logging

from django.views.decorators.csrf import csrf_exempt
import dash.models
import dash.constants
from django.http import JsonResponse, Http404
from django.db.models import F
from django.conf import settings

from utils import request_signer

logger = logging.getLogger(__name__)


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
    return JsonResponse(data)


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
    return JsonResponse(data)


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

    return JsonResponse(data)


@csrf_exempt
def get_ga_accounts(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    all_current_settings = dash.models.AdGroupSettings.objects.all().group_current_settings().prefetch_related(
        'ad_group')
    adgroup_ga_api_enabled = [current_settings.ad_group.id for current_settings in all_current_settings if
                              current_settings.enable_ga_tracking and
                              current_settings.ga_tracking_type == dash.constants.GATrackingType.API]

    ga_accounts = dash.models.GAAnalyticsAccount.objects.filter(
        account__campaign__adgroup__id__in=adgroup_ga_api_enabled).values('account_id', 'ga_account_id',
                                                                          'ga_web_property_id').distinct().order_by(
        'account_id', 'ga_account_id')
    return JsonResponse({'ga_accounts': list(ga_accounts)})
