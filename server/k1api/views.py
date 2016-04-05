import collections
import logging

from django.views.decorators.csrf import csrf_exempt
import dash.models
from django.http import JsonResponse
from django.db.models import F
from django.conf import settings

from utils import request_signer

logger = logging.getLogger(__name__)


def _get_ad_group_source_entities(source_types):
    accounts = (
        dash.models.Account.objects
            .all()
            .exclude_archived()
            .values(
                'id',
                'outbrain_marketer_id',
            )
    )
    account_ids = {account['id'] for account in accounts}

    campaigns = (
        dash.models.Campaign.objects
            .filter(account_id__in=account_ids)
            .exclude_archived()
            .values(
                'id',
                'account_id',
            )
    )
    campaign_ids = {campaign['id'] for campaign in campaigns}

    ad_groups = (
        dash.models.AdGroup.objects
            .filter(campaign_id__in=campaign_ids)
            .exclude_archived()
            .values(
                'id',
                'campaign_id',
            )
    )
    ad_group_ids = {ad_group['id'] for ad_group in ad_groups}

    ad_group_sources = (
        dash.models.AdGroupSource.objects
            .filter(ad_group_id__in=ad_group_ids)
            .exclude(source__maintenance=True,
                     source__deprecated=True)
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

    return accounts, campaigns, ad_groups, ad_group_sources


def _build_ad_group_source_entity_tree(accounts, campaigns, ad_groups, ad_group_sources):
    # index objects by their parent ids
    ad_group_sources_by_ad_group = collections.defaultdict(list)
    for ad_group_source in ad_group_sources:
        ad_group_sources_by_ad_group[ad_group_source['ad_group_id']].append({
            'id': ad_group_source['id'],
            # we need source details per-adgroupsource since source_credentials'
            # source may differ from adgroup source on b1 sources
            'source_name': ad_group_source['source__name'],
            'source_credentials_id': ad_group_source['source_credentials_id'],
            'source_campaign_key': ad_group_source['source_campaign_key'],
        })

    ad_groups_by_campaign = collections.defaultdict(list)
    for ad_group in ad_groups:
        ad_group_id = ad_group['id']
        if not ad_group_sources_by_ad_group[ad_group_id]:
            continue
        ad_groups_by_campaign[ad_group['campaign_id']].append({
            'id': ad_group_id,
            'ad_group_sources': ad_group_sources_by_ad_group[ad_group_id],
        })

    campaigns_by_account = collections.defaultdict(list)
    for campaign in campaigns:
        campaign_id = campaign['id']
        if not ad_groups_by_campaign[campaign_id]:
            continue
        campaigns_by_account[campaign['account_id']].append({
            'id': campaign_id,
            'ad_groups': ad_groups_by_campaign[campaign_id],
        })

    tree = {}
    tree['accounts'] = []
    for account in accounts:
        account_id = account['id']
        if not campaigns_by_account[account_id]:
            continue
        tree['accounts'].append({
            'id': account_id,
            'outbrain_marketer_id': account['outbrain_marketer_id'],
            'campaigns': campaigns_by_account[account_id]
        })

    return tree


def _build_credentials_map(ad_group_sources):
    source_credentials_ids = {ad_group_source['source_credentials_id']
                              for ad_group_source in ad_group_sources}
    source_credentials_list = (
        dash.models.SourceCredentials.objects
        .filter(id__in=source_credentials_ids)
        .values(
            'id',
            'credentials',
            'source__source_type__type',
        )
    )
    credentials_map = {}
    for source_credentials in source_credentials_list:
        credentials_map[source_credentials['id']] = {
            'id': source_credentials['id'],
            'source_type': source_credentials['source__source_type__type'],
            'credentials': source_credentials['credentials'],
        }
    return credentials_map


@csrf_exempt
def get_ad_group_sources(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        return _error_response('Invalid K1 signature.', status=401)

    source_types = request.GET.getlist('source_type')

    accounts, campaigns, ad_groups, ad_group_sources = \
        _get_ad_group_source_entities(source_types)

    # build a tree out of the entities (accounts->campaigns->ad_groups->ad_group_sources)
    entity_tree = _build_ad_group_source_entity_tree(
        accounts,
        campaigns,
        ad_groups,
        ad_group_sources
    )

    # construct a map of credentials that are used by the ad group sources
    credentials_map = _build_credentials_map(ad_group_sources)

    # construct response dict
    data = {}
    data['accounts'] = entity_tree['accounts']
    data['source_credentials_map'] = credentials_map

    return JsonResponse(data)


@csrf_exempt
def get_content_ad_sources(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid K1 signature.')
        return _error_response('Invalid K1 signature.', status=401)

    contentadsources = (
        dash.models.ContentAdSource.objects
        .filter(content_ad__archived=False)
        .filter(source_content_ad_id__isnull=False)
        .annotate(
            ad_group_id=F('content_ad__ad_group_id'),
            source_name=F('source__name'),
        )
        .values(
            'id',
            'source_content_ad_id',
            'content_ad_id',
            'ad_group_id',
            'source_id',
            'source_name',
        )
    )
    ad_group_ids = request.GET.getlist('ad_group')
    if ad_group_ids:
        contentadsources = contentadsources.filter(content_ad__ad_group_id__in=ad_group_ids)
    source_types = request.GET.getlist('source_type')
    if source_types:
        contentadsources = contentadsources.filter(source__source_type__type__in=source_types)

    data = {'content_ad_sources': list(contentadsources)}

    return JsonResponse(data)


def _error_response(error_msg, status=500):
    return JsonResponse({
        'status': 'ERROR',
        'error': error_msg,
    }, status=status)
