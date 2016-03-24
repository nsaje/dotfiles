import collections
import logging

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import dash.models
from django.http import JsonResponse
from django.db.models import Prefetch
from django.db import connection
from django.conf import settings

from utils import request_signer
import sqlparse

logger = logging.getLogger(__name__)


def print_sql(query):
    print sqlparse.format(str(query), reindent=True, keyword_case='upper')


@csrf_exempt
def get_ad_groups(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError as e:
        logger.exception('Invalid K1 signature.')
        return _error_response('Invalid K1 signature.', status=401)

    if settings.DEBUG:
        num_qs_beginning = len(connection.queries)

    source_types_filter = request.GET.getlist('source_type')

    adgroupsources = (
        dash.models.AdGroupSource.objects
            .select_related('source_credentials')
            .values(
                'id',
                'ad_group_id',
                'source_credentials__credentials',
                'source_campaign_key',
                'source__name',
                'source__source_type__type',
            )
    )
    if source_types_filter:
        adgroupsources = adgroupsources.filter(source__source_type__type__in=source_types_filter)

    adgroup_ids = {adgroupsource['ad_group_id'] for adgroupsource in adgroupsources}
    adgroups = (
        dash.models.AdGroup.objects
            .filter(id__in=adgroup_ids)
            .values(
                'id',
                'campaign_id',
            )
    )

    campaign_ids = {adgroup['campaign_id'] for adgroup in adgroups}
    campaigns = (
        dash.models.Campaign.objects
            .filter(id__in=campaign_ids)
            .values(
                'id',
                'account_id',
            )
    )

    conversion_goals = (
        dash.models.ConversionGoal.objects
            .filter(campaign_id__in=campaign_ids)
            .select_related('pixel')
            .values(
                'campaign_id',
                'pixel__slug'
            )
    )

    account_ids = {campaign['account_id'] for campaign in campaigns}
    accounts = (
        dash.models.Account.objects
            .filter(id__in=account_ids)
            .values(
                'id',
                'outbrain_marketer_id',
            )
    )

    adgroupsources_by_adgroup = collections.defaultdict(list)
    for adgroupsource in adgroupsources:
        adgroupsources_by_adgroup[adgroupsource['ad_group_id']].append({
            'id': adgroupsource['id'],
            'source_name': adgroupsource['source__name'],
            'source_type': adgroupsource['source__source_type__type'],
            'source_credentials': adgroupsource['source_credentials__credentials'],
            'source_campaign_key': adgroupsource['source_campaign_key'],
        })

    adgroups_by_campaign = collections.defaultdict(list)
    for adgroup in adgroups:
        adgroup_id = adgroup['id']
        adgroups_by_campaign[adgroup['campaign_id']].append({
            'id': adgroup_id,
            'adgroupsources': adgroupsources_by_adgroup[adgroup_id],
        })

    conversion_goals_by_campaign = collections.defaultdict(list)
    for conversion_goal in conversion_goals:
        conversion_goals_by_campaign[conversion_goal['campaign_id']].append(conversion_goal)

    campaigns_by_account = collections.defaultdict(list)
    for campaign in campaigns:
        campaign_id = campaign['id']
        campaigns_by_account[campaign['account_id']].append({
            'id': campaign_id,
            'ad_groups': adgroups_by_campaign[campaign_id],
            'conversion_goals': conversion_goals_by_campaign[campaign_id],
        })

    data = {}
    data['accounts'] = []
    for account in accounts:
        account_id = account['id']
        data['accounts'].append({
            'id': account_id,
            'outbrain_marketer_id': account['outbrain_marketer_id'],
            'campaigns': campaigns_by_account[account_id]
        })

    if settings.DEBUG:
        import json
        print json.dumps(data, indent=4)
        num_qs = len(connection.queries) - num_qs_beginning
        for q in connection.queries[-num_qs:]:
            print_sql(q['sql'])
        print 'Queries run:', num_qs
    return JsonResponse(data)


@csrf_exempt
def get_content_ad_sources(request):
    try:
        request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    except request_signer.SignatureError as e:
        logger.exception('Invalid K1 signature.')
        return _error_response('Invalid K1 signature.', status=401)

    if settings.DEBUG:
        num_qs_beginning = len(connection.queries)

    contentadsources = (
        dash.models.ContentAdSource.objects
        .values(
            'id',
            'content_ad_id',
            'content_ad__ad_group_id',
            'source__id',
            'source__tracking_slug',
            'source__source_type__type',
            'source_content_ad_id',
        )
    )
    adgroup_ids = request.GET.getlist('ad_group')
    if adgroup_ids:
        contentadsources = contentadsources.filter(content_ad__ad_group_id__in=adgroup_ids)
    source_types = request.GET.getlist('source_type')
    if source_types:
        contentadsources = contentadsources.filter(source__source_type__type__in=source_types)

    # FIXME
    # slice it
    contentadsources = contentadsources[:10]

    data_by_ids = {}
    for contentadsource in contentadsources:
        adgroup_id = contentadsource['content_ad__ad_group_id']
        if adgroup_id not in data_by_ids:
            data_by_ids[adgroup_id] = dict()
        content_ad_id = contentadsource['content_ad_id']
        if content_ad_id not in data_by_ids[adgroup_id]:
            data_by_ids[adgroup_id][content_ad_id] = list()
        data_by_ids[adgroup_id][content_ad_id].append(contentadsource)

    data = {'ad_groups': []}
    for adgroup_id, content_ads_dict in data_by_ids.items():
        content_ads = []
        for content_ad_id, content_ad_sources_raw in content_ads_dict.items():
            content_ad_sources = []
            for content_ad_source in content_ad_sources_raw:
                content_ad_sources.append({
                    'id': content_ad_source['id'],
                    'source_id': content_ad_source['source__id'],
                    'source_tracking_slug': content_ad_source['source__tracking_slug'],
                    'source_type': content_ad_source['source__source_type__type'],
                    'source_content_ad_id': content_ad_source['source_content_ad_id'],
                })
            content_ads.append({
                'id': content_ad_id,
                'content_ad_sources': content_ad_sources,
            })
        data['ad_groups'].append({
            'id': adgroup_id,
            'content_ads': content_ads,
        })

    if settings.DEBUG:
        import json
        print json.dumps(data, indent=4)
        num_qs = len(connection.queries) - num_qs_beginning
        for q in connection.queries[-num_qs:]:
            print_sql(q['sql'])
        print 'Queries run:', num_qs

    return JsonResponse(data)


def _error_response(error_msg, status=500):
    return JsonResponse({
        'status': 'ERROR',
        'error': error_msg,
    }, status=status)
