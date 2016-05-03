import json
import logging
from django.conf import settings
from django.db.models import F, Q
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import dash.constants
import dash.models
from dash import constants, publisher_helpers
from utils import url_helper, request_signer


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
            slug=F('source__bidder_slug'),
        )
        .values(
            'source_content_ad_id',
            'content_ad_id',
            'ad_group_id',
            'source_name',
            'slug',
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
def get_sources_by_tracking_slug(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    data = {}

    sources = dash.models.Source.objects.all()
    for source in sources:
        data[source.tracking_slug] = {
            'id': source.id,
        }

    return _response_ok(data)


@csrf_exempt
def get_accounts_slugs_ad_groups(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        raise Http404

    accounts = [int(account) for account in request.GET.getlist('account')]

    data = {account: {'slugs': [], 'ad_groups': {}} for account in accounts}

    conversion_pixels = (dash.models.ConversionPixel.objects
                         .filter(account_id__in=accounts)
                         .filter(archived=False))
    for conversion_pixel in conversion_pixels:
        data[conversion_pixel.account_id]['slugs'].append(conversion_pixel.slug)

    ad_groups = (dash.models.AdGroup.objects.all()
                 .exclude_archived()
                 .select_related('campaign')
                 .filter(campaign__account_id__in=accounts))
    for ad_group in ad_groups:
        data[ad_group.campaign.account_id]['ad_groups'][ad_group.id] = {
            'campaign_id': ad_group.campaign_id,
        }

    return _response_ok(data)


@csrf_exempt
def get_publishers_blacklist(request):
    _validate_signature(request)

    ad_group_id = request.GET.get('ad_group_id')
    if ad_group_id:
        ad_group = dash.models.AdGroup.objects.get(id=ad_group_id)
        blacklist_filter = Q(ad_group=ad_group) | Q(campaign=ad_group.campaign) | Q(account=ad_group.campaign.account)
        blacklisted = (dash.models.PublisherBlacklist.objects
                       .filter(blacklist_filter)
                       .select_related('source', 'ad_group'))
    else:
        running_ad_groups = dash.models.AdGroup.objects.all().filter_running().select_related('campaign',
                                                                                              'campaign__account')
        running_campaigns = set([ag.campaign for ag in running_ad_groups])
        running_accounts = set([c.account for c in running_campaigns])

        blacklist_filter = (Q(ad_group__isnull=True, campaign__isnull=True, account__isnull=True) |
                            Q(ad_group__in=running_ad_groups) |
                            Q(campaign__in=running_campaigns) |
                            Q(account__in=running_accounts))
        blacklisted = (dash.models.PublisherBlacklist.objects
                       .filter(blacklist_filter)
                       .select_related('source', 'ad_group',  'campaign', 'account', 'account')
                       .prefetch_related('campaign__adgroup_set',
                                         'account__campaign_set',
                                         'account__campaign_set__adgroup_set'))

    blacklist = {}
    for item in blacklisted:
        exchange = None
        if item.source is not None:
            exchange = publisher_helpers.publisher_exchange(item.source)

        # for single ad group ad_group_id is always the one queried
        if ad_group_id:
            entry = {
                'ad_group_id': ad_group.id,
                'domain': item.name,
                'exchange': exchange,
                'status': item.status,
                'external_id': item.external_id,
            }
            blacklist[hash(tuple(entry.values()))] = entry
        # for all ad groups generate all ad_group_ids
        else:
            _process_item(blacklist, item, exchange, running_ad_groups)

    return _response_ok({'blacklist': list(blacklist.values())})


def _process_item(blacklist, item, exchange, running_ad_groups):
    # if ad_group then use this ad_group_id
    if item.ad_group:
        entry = {
            'ad_group_id': item.ad_group_id,
            'domain': item.name,
            'exchange': exchange,
            'status': item.status,
            'external_id': item.external_id,
        }
        blacklist[hash(tuple(entry.values()))] = entry
    # if campaign then generate all running ad groups is this campaign
    elif item.campaign:
        _process_campaign(blacklist, item, item.campaign, exchange, running_ad_groups)
    # if account then generate all running ad groups in this account
    elif item.account:
        for campaign in item.account.campaign_set.all():
            _process_campaign(blacklist, item, campaign, exchange, running_ad_groups)
    # global blacklist
    else:
        entry = {
            'ad_group_id': None,
            'domain': item.name,
            'exchange': exchange,
            'status': item.status,
            'external_id': item.external_id,
        }
        blacklist[hash(tuple(entry.values()))] = entry


def _process_campaign(blacklist, item, campaign, exchange, running_ad_groups):
    for ad_group in campaign.adgroup_set.all():
        if ad_group in running_ad_groups:
            entry = {
                'ad_group_id': ad_group.id,
                'domain': item.name,
                'exchange': exchange,
                'status': item.status,
                'external_id': item.external_id,
            }
            blacklist[hash(tuple(entry.values()))] = entry


@csrf_exempt
def get_ad_groups(request):
    _validate_signature(request)

    ad_group_id = request.GET.get('ad_group_id')
    ad_groups_settings, campaigns_settings_map = _get_ad_groups_and_campaigns_settings(ad_group_id)

    ad_groups = []
    for ad_group_settings in ad_groups_settings:
        ad_group = {
            'id': ad_group_settings.ad_group.id,
            'name': ad_group_settings.ad_group.name,
            'start_date': ad_group_settings.start_date,
            'end_date': ad_group_settings.end_date,
            'time_zone': settings.DEFAULT_TIME_ZONE,
            'brand_name': ad_group_settings.brand_name,
            'display_url': ad_group_settings.display_url,
            'tracking_codes': ad_group_settings.get_tracking_codes(),
            'device_targeting': ad_group_settings.target_devices,
            'iab_category': campaigns_settings_map[ad_group_settings.ad_group.campaign.id].iab_category,
            'target_regions': ad_group_settings.target_regions,
            'retargeting_ad_groups': ad_group_settings.retargeting_ad_groups,
        }

        ad_groups.append(ad_group)

    return _response_ok(ad_groups)


def _get_ad_groups_and_campaigns_settings(ad_group_id):
    ad_groups_settings = (dash.models.AdGroupSettings.objects
                          .group_current_settings()
                          .select_related('ad_group', 'ad_group__campaign'))
    if ad_group_id:
        ad_groups_settings = ad_groups_settings.filter(ad_group__id=ad_group_id)
        ad_group_ids = [ad_group_id]
    else:
        ad_group_ids = [ad_group_settings.ad_group_id for ad_group_settings in ad_groups_settings if
                        not ad_group_settings.archived]

    campaigns_settings = (dash.models.CampaignSettings.objects
                          .filter(campaign__adgroup__id__in=ad_group_ids)
                          .group_current_settings()
                          .select_related('campaign'))
    campaigns_settings_map = {cs.campaign.id: cs for cs in campaigns_settings}

    return ad_groups_settings, campaigns_settings_map


@csrf_exempt
def get_ad_groups_exchanges(request):
    _validate_signature(request)

    ad_group_id = request.GET.get('ad_group_id')
    ad_group_sources_settings = _get_ad_group_sources_settings(ad_group_id)

    ad_group_sources = {}
    for ad_group_source_setting in ad_group_sources_settings:
        ad_group_id = ad_group_source_setting.ad_group_source.ad_group.id
        source = {
            'exchange': ad_group_source_setting.ad_group_source.source.bidder_slug,
            'status': ad_group_source_setting.state,
            'cpc_cc': ad_group_source_setting.cpc_cc,
            'daily_budget_cc': ad_group_source_setting.daily_budget_cc,
        }
        ad_group_sources.setdefault(ad_group_id, []).append(source)

    return _response_ok(ad_group_sources)


def _get_ad_group_sources_settings(ad_group_id):
    if ad_group_id:
        ad_group_sources_settings = (dash.models.AdGroupSourceSettings.objects
                                     .filter(ad_group_source__ad_group__id=ad_group_id,
                                             ad_group_source__source__source_type__type='b1')
                                     .group_current_settings()
                                     .select_related('ad_group_source',
                                                     'ad_group_source__source',
                                                     'ad_group_source__ad_group'))
    else:
        ad_groups = (dash.models.AdGroupSettings.objects.filter(archived=False).group_current_settings()
                     .select_related('ad_group')
                     .values_list('ad_group', flat=True))
        ad_group_sources_settings = (dash.models.AdGroupSourceSettings.objects
                                     .filter(ad_group_source__ad_group__in=ad_groups,
                                             ad_group_source__source__source_type__type='b1')
                                     .group_current_settings()
                                     .select_related('ad_group_source',
                                                     'ad_group_source__source',
                                                     'ad_group_source__ad_group'))

    return ad_group_sources_settings



