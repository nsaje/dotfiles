import collections

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import dash.models
from django.http import JsonResponse
from django.db.models import Prefetch
from django.db import connection
from django.conf import settings

import sqlparse


def print_sql(query):
    print sqlparse.format(str(query), reindent=True, keyword_case='upper')


@csrf_exempt
def get_campaign_data(request, media_source=None):
    # FIXME
    # try:
    #     request_signer.verify_wsgi_request(request, settings.K1_API_SIGN_KEY)
    # except request_signer.SignatureError as e:
    #     logger.exception('Invalid K1 signature.')
    #     return _error_response('Invalid K1 signature.', status=401)

    if settings.DEBUG:
        num_qs_beginning = len(connection.queries)

    content_ads = (
        dash.models.ContentAd.objects
           .select_related('ad_group__campaign__account')
           .prefetch_related(Prefetch(
               'contentadsource_set',
               to_attr='filtered_sources',
               queryset=dash.models.ContentAdSource.objects
               .select_related('source')
               .only(
                   'id',
                   'content_ad_id',
                   'source__id',
                   'source__tracking_slug',
                   'source_content_ad_id',
               )
           ))
           # .prefetch_related('ad_group__campaign__account__conversionpixel_set')
           .values(
               'ad_group__campaign__account__id',
               'ad_group__campaign__account__outbrain_marketer_id',
               'ad_group__campaign__id',
               'ad_group__id',
               'id',
               'contentadsource__id',
               'contentadsource__content_ad_id',
               'contentadsource__source__id',
               'contentadsource__source__tracking_slug',
               'contentadsource__source_content_ad_id',
           )
    )[:1]

    import pprint
    pprint.pprint(content_ads)
    response_data = {}

    # for content_ad in content_ads:
    #     # pprint.pprint(dir(content_ad))
    #     print content_ad.ad_group.campaign.id
    #     print content_ad.ad_group.campaign.account.id
    #     for contentadsource in content_ad.filtered_sources:
    #         print contentadsource.source.id

    # def tree(): return collections.defaultdict(tree)
    # data = tree()
    # for ca in content_ads:
    #     sources = []
    #     for cas in ca.filtered_sources:
    #         sources.append({
    #             'id': cas.id,
    #             'source_id': cas.source.id,
    #             'source_id': cas.source.id,
    #             'source_slug': cas.source.tracking_slug,
    #             'source_content_ad_id': cas.source_content_ad_id,
    #         })
    #     data[ca.ad_group.campaign.account.id][
    #         ca.ad_group.campaign.id][ca.ad_group.id][ca.id] = sources
    #
    # accounts = []
    # for account_id in data.keys():
    #     campaigns = []
    #     for campaign_id in data[account_id].keys():
    #         ad_groups = []
    #         for adgroup_id in data[account_id][campaign_id].keys():
    #             content_ads = []
    #             for content_ad_id in data[account_id][campaign_id][adgroup_id].keys():
    #                 content_ads.append({
    #                     'id': content_ad_id,
    #                     'content_ad_sources': data[account_id][campaign_id][adgroup_id][content_ad_id]
    #                 })
    #             ad_groups.append({
    #                 'id': adgroup_id,
    #                 'content_ads': content_ads
    #             })
    #         campaigns.append({
    #             'id': campaign_id,
    #             'ad_groups': ad_groups
    #         })
    #     accounts.append({
    #         'id': account_id,
    #         'campaigns': campaigns
    #     })
    # response_data = {
    #     'accounts': accounts
    # }
    #
    if settings.DEBUG:
        import pprint
        print response_data
        num_qs = len(connection.queries) - num_qs_beginning
        for q in connection.queries[-num_qs:]:
            print_sql(q['sql'])
        print 'Queries run:', num_qs
    #
    return JsonResponse(response_data)
