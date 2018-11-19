import json
import logging
import random
from collections import defaultdict

import influx
from django.conf import settings
from django.http import Http404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import dash.api
import dash.constants
import dash.models
from dash.features import contentupload
from integrations.bizwire import config
from integrations.bizwire.internal import actions
from integrations.bizwire.internal import helpers
from utils import k1_helper
from utils import request_signer

logger = logging.getLogger(__name__)


@csrf_exempt
@influx.timer("integrations.bizwire.internal.views.click_capping")
def click_capping(request):
    try:
        request_signer.verify_wsgi_request(request, settings.R1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception("Invalid signature.")
        raise Http404

    content_ad_id = int(request.GET.get("creativeId"))
    logger.info("[bizwire] click capping - content ad id: %s", content_ad_id)

    content_ad = (
        dash.models.ContentAd.objects.filter(id=content_ad_id, ad_group__campaign_id=config.AUTOMATION_CAMPAIGN)
        .select_related("ad_group__campaign")
        .get()
    )

    if content_ad.state != dash.constants.ContentAdSourceState.INACTIVE:
        content_ad.state = dash.constants.ContentAdSourceState.INACTIVE
        content_ad.save()

    for content_ad_source in content_ad.contentadsource_set.all():
        if content_ad_source.state != dash.constants.ContentAdSourceState.INACTIVE:
            content_ad_source.state = dash.constants.ContentAdSourceState.INACTIVE
            content_ad_source.save()

    k1_helper.update_content_ad(content_ad, msg="bizwire.click_capping")
    return JsonResponse({"status": "ok"})


def _distribute_articles(articles_data):
    existing_candidate_labels = dash.models.ContentAdCandidate.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN, label__in=[article["label"] for article in articles_data]
    ).values_list("label", flat=True)

    existing_contentad_labels = dash.models.ContentAd.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN, label__in=[article["label"] for article in articles_data]
    ).values_list("label", flat=True)

    candidates_per_ad_group = defaultdict(list)
    for article in articles_data:
        if article["label"] in existing_candidate_labels or article["label"] in existing_contentad_labels:
            # prevent inserting multiple times if calls are repeated
            continue

        ad_group_id = helpers.get_current_ad_group_id()
        candidates_per_ad_group[ad_group_id].append(article)

    return candidates_per_ad_group


@csrf_exempt
@influx.timer("integrations.bizwire.internal.views.article_upload")
def article_upload(request):
    try:
        request_signer.verify_wsgi_request(request, settings.LAMBDA_CONTENT_UPLOAD_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception("Invalid signature.")
        raise Http404

    articles_data = json.loads(request.body)

    labels = [article["label"] for article in articles_data]
    logger.info("[bizwire] article upload - uploading articles with labels: %s", labels)

    candidates_per_ad_group = _distribute_articles(articles_data)
    for ad_group_id, candidates_data in candidates_per_ad_group.items():
        batch_name = "Article " + candidates_data[0]["label"]
        if len(candidates_data) > 1:
            batch_name = "Multiple articles upload"

        ad_group = dash.models.AdGroup.objects.get(id=ad_group_id, campaign_id=config.AUTOMATION_CAMPAIGN)

        contentupload.upload.insert_candidates(
            None, ad_group.campaign.account, candidates_data, ad_group, batch_name, filename="no-verify", auto_save=True
        )

    for ad_group_id in list(candidates_per_ad_group.keys()):
        try:
            if random.random() > 0.9:
                actions.recalculate_and_set_new_daily_budgets(ad_group_id)
        except Exception:
            logger.exception("Unable to set new bizwire daily budget for ad group %s", ad_group_id)

    return JsonResponse({"status": "ok"})
