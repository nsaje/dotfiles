import json
import logging

import datetime
from dateutil import tz
from django.views.decorators.csrf import csrf_exempt
import dash.models
import dash.constants
from django.http import JsonResponse, Http404
from django.db.models import F, Q
from django.conf import settings

from dash import constants
from k1api import codelists
from utils import url_helper, request_signer

logger = logging.getLogger(__name__)

EVENT_RETARGET_ADGROUP = "redirect_adgroup"


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


def _validate_signature(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404


@csrf_exempt
def get_ad_group_source_ids(request):
    _validate_signature(request)

    credentials_id = request.GET.get('credentials_id')
    if not credentials_id:
        _response_error("Missing credentials ID")

    nonarchived = dash.models.AdGroup.objects.all().exclude_archived()
    ad_group_sources = (
        dash.models.AdGroupSource.objects
            .filter(ad_group__in=nonarchived)
            .filter(source_credentials_id=credentials_id)
            .values(
                'ad_group_id',
                'source_campaign_key',
            )
    )
    return _response_ok(list(ad_group_sources))


@csrf_exempt
def get_ad_group_source(request):
    _validate_signature(request)

    ad_group_id = request.GET.get('ad_group_id')
    if not ad_group_id:
        return _response_error("Must provide ad group id.")
    source_type = request.GET.get('source_type')
    if not source_type:
        return _response_error("Must provide source type.")

    try:
        ad_group_source = (
            dash.models.AdGroupSource.objects
            .get(
                ad_group_id=ad_group_id,
                source__source_type__type=source_type,
            )
        )
    except dash.models.AdGroupSource.DoesNotExist:
        return _response_error("The ad group %s is not present on source %s" %
                               (ad_group_id, source_type), status=404)

    ad_group_source_settings = ad_group_source.get_current_settings()
    ad_group_settings = ad_group_source.ad_group.get_current_settings()

    data = {
        'ad_group_source_id': ad_group_source.id,
        'ad_group_id': ad_group_source.ad_group_id,
        'credentials': ad_group_source.source_credentials.credentials,
        'source_campaign_key': ad_group_source.source_campaign_key,
        'state': ad_group_source_settings.state,
        'cpc_cc': ad_group_source_settings.cpc_cc,
        'daily_budget_cc': ad_group_source_settings.daily_budget_cc,
        'name': ad_group_source.get_external_name(),
        'start_date': ad_group_settings.start_date,
        'end_date': ad_group_settings.start_date,
        'target_devices': ad_group_settings.target_devices,
        'target_regions': ad_group_settings.target_regions,
    }
    return _response_ok(data)


@csrf_exempt
def get_content_ad_sources_for_ad_group(request):
    _validate_signature(request)

    source_type = request.GET.get('source_type')
    if not source_type:
        return _response_error("Must provide source type.")
    ad_group_id = request.GET.get('ad_group_id', None)
    if not ad_group_id:
        return _response_error("Must provide ad group id.")
    content_ad_id = request.GET.get('content_ad_id', None)

    logger.info(ad_group_id)
    logger.info(source_type)
    ad_group_source = (
        dash.models.AdGroupSource.objects
            .select_related('ad_group', 'source')
            .get(
                ad_group_id=ad_group_id,
                source__source_type__type=source_type
            )
    )

    content_ad_sources = (
        dash.models.ContentAdSource.objects
        .select_related('content_ad')
        .filter(content_ad__ad_group_id=ad_group_id)
        .filter(source__source_type__type=source_type)
        .exclude(submission_status=constants.ContentAdSubmissionStatus.REJECTED)
    )
    if content_ad_id:
        content_ad_sources = content_ad_sources.filter(content_ad_id=content_ad_id)

    ad_group_tracking_codes = None
    if ad_group_source.source.update_tracking_codes_on_content_ads() and\
            ad_group_source.can_manage_content_ads:
        ad_group_tracking_codes = ad_group_source.ad_group.get_current_settings().get_tracking_codes()

    content_ads = []
    for content_ad_source in content_ad_sources:
        if ad_group_tracking_codes:
            url = content_ad_source.content_ad.url_with_tracking_codes(
                url_helper.combine_tracking_codes(
                    ad_group_tracking_codes,
                    ad_group_source.get_tracking_ids(),
                )
            )
        else:
            url = content_ad_source.content_ad.url

        content_ads.append({
            'credentials': ad_group_source.source_credentials.credentials,
            'source_campaign_key': ad_group_source.source_campaign_key,
            'ad_group_id': content_ad_source.content_ad.ad_group_id,
            'content_ad_id': content_ad_source.content_ad_id,
            'source_content_ad_id': content_ad_source.source_content_ad_id,
            'state': content_ad_source.state,
            'title': content_ad_source.content_ad.title,
            'url': url,
            'submission_status': content_ad_source.submission_status,
            'image_id': content_ad_source.content_ad.image_id,
            'image_width': content_ad_source.content_ad.image_width,
            'image_height': content_ad_source.content_ad.image_height,
            'image_hash': content_ad_source.content_ad.image_hash,
            'redirect_id': content_ad_source.content_ad.redirect_id,
            'display_url': content_ad_source.content_ad.display_url,
            'brand_name': content_ad_source.content_ad.brand_name,
            'description': content_ad_source.content_ad.description,
            'call_to_action': content_ad_source.content_ad.call_to_action,
            'tracking_slug': ad_group_source.source.tracking_slug,
            'tracker_urls': content_ad_source.content_ad.tracker_urls
        })
    return _response_ok(list(content_ads))


@csrf_exempt
def get_accounts(request):
    _validate_signature(request)

    accounts_list = (
        dash.models.Account.objects
            .all()
            .exclude_archived()
            .values(
                'id',
                'outbrain_marketer_id',
            )
    )

    return _response_ok({'accounts': list(accounts_list)})


@csrf_exempt
def get_source_credentials_for_reports_sync(request):
    _validate_signature(request)

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

    return _response_ok({'source_credentials_list': list(source_credentials_list)})


@csrf_exempt
def get_content_ad_source_mapping(request):
    _validate_signature(request)

    source_content_ad_ids = json.loads(request.body)
    if not isinstance(source_content_ad_ids, list):
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

    return _response_ok({'content_ad_sources': list(contentadsources)})


@csrf_exempt
def get_ga_accounts(request):
    _validate_signature(request)

    all_current_settings = dash.models.AdGroupSettings.objects.all().group_current_settings().prefetch_related(
        'ad_group')
    adgroup_ga_api_enabled = [current_settings.ad_group.id for current_settings in all_current_settings if
                              current_settings.enable_ga_tracking and
                              current_settings.ga_tracking_type == dash.constants.GATrackingType.API]

    ga_accounts = (dash.models.GAAnalyticsAccount.objects
                   .filter(account__campaign__adgroup__id__in=adgroup_ga_api_enabled)
                   .values('account_id', 'ga_account_id', 'ga_web_property_id')
                   .distinct()
                   .order_by('account_id', 'ga_account_id'))
    return _response_ok({'ga_accounts': list(ga_accounts)})


@csrf_exempt
def get_publishers_blacklist(request):
    _validate_signature(request)

    ad_group_id = request.GET.get('ad_group_id')
    if ad_group_id is not None:
        blacklisted = (dash.models.PublisherBlacklist.objects
                       .filter(ad_group__id=ad_group_id)
                       .values('name', 'ad_group_id', 'source__tracking_slug', 'status'))
    else:
        current_settings = dash.models.AdGroupSettings.objects.all().group_current_settings().select_related(
            'ad_group')

        running_ad_groups = []
        for ad_group_settings in current_settings:
            if ad_group_settings.ad_group.get_running_status_by_flight_time(
                    ad_group_settings) == constants.AdGroupRunningStatus.ACTIVE:
                running_ad_groups.append(ad_group_settings.ad_group.id)

        blacklisted = (dash.models.PublisherBlacklist.objects
                       .filter(Q(ad_group__isnull=True) | Q(ad_group__id__in=running_ad_groups))
                       .values('name', 'ad_group_id', 'source__tracking_slug', 'status'))

    blacklist = []
    for item in blacklisted:
        exchange = None
        if item.get('source__tracking_slug') is not None:
            exchange = item['source__tracking_slug'].replace('b1_', '')

        blacklist.append({
            'ad_group_id': item.get('ad_group_id'),
            'domain': item['name'],
            'exchange': exchange,
            'status': item['status']
        })

    return _response_ok({'blacklist': blacklist})


@csrf_exempt
def get_ad_groups(request):
    _validate_signature(request)

    ad_group_id = request.GET.get('ad_group_id')
    if ad_group_id is not None:
        ad_groups_settings = dash.models.AdGroupSettings.objects.filter(
            ad_group__id=ad_group_id).group_current_settings().select_related('ad_group', 'ad_group__campaign')
    else:
        ad_groups_settings = dash.models.AdGroupSettings.objects.all().group_current_settings().select_related(
            'ad_group', 'campaign')

    ad_group_ids = [ad_group_settings.ad_group_id for ad_group_settings in ad_groups_settings]
    campaigns_settings = dash.models.CampaignSettings.objects.filter(
        campaign__adgroup__id__in=ad_group_ids).select_related('campaign')
    campaigns_settings_map = {cs.campaign.id: cs for cs in campaigns_settings}

    from_tz = tz.gettz(settings.DEFAULT_TIME_ZONE)
    to_tz = tz.gettz('UTC')

    ad_groups = []
    for ad_group_settings in ad_groups_settings:
        ad_group = {
            'id': ad_group_settings.ad_group.id,
            'name': ad_group_settings.ad_group.name,
            'startDt': datetime.datetime.combine(ad_group_settings.start_date, datetime.datetime.min.time()).replace(
                tzinfo=from_tz).astimezone(to_tz).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'brandName': ad_group_settings.brand_name,
            'displayUrl': ad_group_settings.display_url,
            'trackingCodes': ad_group_settings.get_tracking_codes(),
            'deviceTargeting': ad_group_settings.target_devices,
        }

        if ad_group_settings.end_date:
            day = datetime.timedelta(days=1)
            ad_group['endDt'] = datetime.datetime.combine(ad_group_settings.end_date + day,
                                                            datetime.datetime.min.time()).replace(
                tzinfo=from_tz).astimezone(to_tz).strftime('%Y-%m-%dT%H:%M:%SZ')

        campaign_settings = campaigns_settings_map[ad_group_settings.ad_group.campaign.id]
        ad_group['iabCategory'] = campaign_settings.iab_category

        # divide ad group settings target regions
        geo_targeting = []
        subdivision_targeting = []
        dma_targeting = []

        # separate countries, subdivisions and DMAs
        for tr in ad_group_settings.target_regions:
            if tr in codelists.DMA_WOEID:
                dma_targeting.append(int(tr))
            elif tr in codelists.SUBDIVISION_WOEID:
                subdivision_targeting.append(_translate_subdivision(tr))
            elif tr in codelists.COUNTRY_CODE_WOEID:
                geo_targeting.append(tr)

        ad_group['geoTargeting'] = geo_targeting
        ad_group['dmaTargeting'] = dma_targeting
        ad_group['regionTargeting'] = subdivision_targeting

        # retargeting ad groups
        retargeting_blob = []
        for ad_group_id in ad_group_settings.retargeting_ad_groups:
            retargeting_blob.append({
                'event_type': EVENT_RETARGET_ADGROUP,
                'event_id': '{}'.format(ad_group_id),
            })
        ad_group['retargetings'] = retargeting_blob

        ad_groups.append(ad_group)

    return _response_ok(ad_groups)


def _translate_subdivision(subdivision):
    if subdivision.startswith('US-'):
        return subdivision[3:]
    else:
        return subdivision

