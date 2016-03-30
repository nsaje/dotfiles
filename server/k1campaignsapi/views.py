import collections
import logging

from django.views.decorators.csrf import csrf_exempt
import dash.models
from django.http import JsonResponse
from django.db.models import F
from django.conf import settings

from utils import request_signer
import sqlparse

logger = logging.getLogger(__name__)


def print_sql(query):
    print sqlparse.format(str(query), reindent=True, keyword_case='upper')


@csrf_exempt
def get_ad_group_sources(request):
    # try:
    #     request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    # except request_signer.SignatureError as e:
    #     logger.exception('Invalid K1 signature.')
    #     return _error_response('Invalid K1 signature.', status=401)

    source_types_filter = request.GET.getlist('source_type')

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
            .values(
                'id',
                'ad_group_id',
                'source_credentials_id',
                'source__name',
                'source_campaign_key',
            )
    )
    if source_types_filter:
        ad_group_sources = ad_group_sources.filter(
            source__source_type__type__in=source_types_filter)

    # if not include_maintenance:
    ad_group_sources = ad_group_sources.exclude(source__maintenance=True)

    # if not include_deprecated:
    ad_group_sources = ad_group_sources.exclude(source__deprecated=True)

    # first, partition by source credentials
    ad_group_sources_by_source_credentials = collections.defaultdict(list)
    for ad_group_source in ad_group_sources:
        ad_group_sources_by_source_credentials[
            ad_group_source['source_credentials_id']].append(ad_group_source)

    # build object tree per source credentials
    # FIXME rename ad_group_sources to something indicating it's per-source-credentials
    source_credentials_entities = []
    for source_credentials_id, ad_group_sources in ad_group_sources_by_source_credentials.items():
        # index objects by their parent ids
        ad_group_sources_by_ad_group = collections.defaultdict(list)
        for ad_group_source in ad_group_sources:
            ad_group_sources_by_ad_group[ad_group_source['ad_group_id']].append({
                'id': ad_group_source['id'],
                'source_credentials_id': ad_group_source['source_credentials_id'],
                'source_campaign_key': ad_group_source['source_campaign_key'],
                # we need source details per-adgroupsource since source_credentials'
                # source may differ from adgroup source on b1 sources
                'source_name': ad_group_source['source__name'],
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

        source_credentials_accounts = []
        for account in accounts:
            account_id = account['id']
            if not campaigns_by_account[account_id]:
                continue
            source_credentials_accounts.append({
                'id': account_id,
                'outbrain_marketer_id': account['outbrain_marketer_id'],
                'campaigns': campaigns_by_account[account_id]
            })

        source_credentials = (
            dash.models.SourceCredentials.objects
            .only(
                'credentials',
                'source__source_type__type',
            )
            .get(pk=source_credentials_id)
        )
        source_credentials_entities.append({
            'source_type': source_credentials.source.source_type.type,
            'credentials': source_credentials.credentials,
            'accounts': source_credentials_accounts,
        })

    # construct response dict
    data = {}
    data['source_credentials'] = source_credentials_entities

    return JsonResponse(data)


@csrf_exempt
def get_content_ad_sources(request):
    # try:
    #     request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    # except request_signer.SignatureError as e:
    #     logger.exception('Invalid K1 signature.')
    #     return _error_response('Invalid K1 signature.', status=401)

    contentadsources = (
        dash.models.ContentAdSource.objects
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
