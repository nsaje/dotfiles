from collections import defaultdict
import logging
import json

from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction

from integrations.bizwire import config, models
from integrations.bizwire.internal import actions, helpers

import dash.api
import dash.constants
import dash.models
import dash.upload

from utils import k1_helper, request_signer

logger = logging.getLogger(__name__)


@csrf_exempt
def click_capping(request):
    try:
        request_signer.verify_wsgi_request(request, settings.R1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid signature.')
        raise Http404

    content_ad_id = int(request.GET.get('creativeId'))
    logger.info('[bizwire] click capping - content ad id: %s', content_ad_id)

    content_ad = dash.models.ContentAd.objects.filter(
        id=content_ad_id,
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
    ).select_related('ad_group').get()

    with transaction.atomic():
        dash.api.update_content_ads_state([content_ad], dash.constants.ContentAdSourceState.INACTIVE, None)
        k1_helper.update_content_ad(content_ad.ad_group.id, content_ad.id)

    return JsonResponse({
        "status": 'ok'
    })


def _get_ad_group_id(article):
    if article.get('meta', {}).get('is_test_feed', False):
        return config.TEST_FEED_AD_GROUP

    today = helpers.get_pacific_now().date()
    return models.AdGroupTargeting.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
        start_date__lte=today, interest_targeting=[]
    ).latest('start_date').ad_group_id


def _distribute_articles(articles_data):
    existing_candidate_labels = dash.models.ContentAdCandidate.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
        label__in=[article['label'] for article in articles_data],
    ).values_list('label', flat=True)

    existing_contentad_labels = dash.models.ContentAd.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
        label__in=[article['label'] for article in articles_data],
    ).values_list('label', flat=True)

    candidates_per_ad_group = defaultdict(list)
    for article in articles_data:
        if article['label'] in existing_candidate_labels or article['label'] in existing_contentad_labels:
            # prevent inserting multiple times if calls are repeated
            continue

        ad_group_id = _get_ad_group_id(article)
        if 'meta' in article:
            del article['meta']

        candidates_per_ad_group[ad_group_id].append(article)

    return candidates_per_ad_group


@csrf_exempt
def article_upload(request):
    try:
        request_signer.verify_wsgi_request(request, settings.LAMBDA_CONTENT_UPLOAD_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid signature.')
        raise Http404

    articles_data = json.loads(request.body)

    labels = [article['label'] for article in articles_data]
    logger.info('[bizwire] article upload - uploading articles with labels: %s', labels)

    candidates_per_ad_group = _distribute_articles(articles_data)
    for ad_group_id, candidates_data in candidates_per_ad_group.iteritems():
        batch_name = 'Article ' + candidates_data[0]['label']
        if len(candidates_data) > 1:
            batch_name = 'Multiple articles upload'

        ad_group = dash.models.AdGroup.objects.get(
            id=ad_group_id,
            campaign_id=config.AUTOMATION_CAMPAIGN,
        )

        dash.upload.insert_candidates(candidates_data, ad_group, batch_name, filename='', auto_save=True)

    for ad_group_id in candidates_per_ad_group.keys():
        try:
            actions.recalculate_and_set_new_daily_budgets(ad_group_id)
        except:
            logger.exception('Unable to set new bizwire daily budget for ad group %s', ad_group_id)

    return JsonResponse({
        "status": 'ok'
    })
