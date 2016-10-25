import logging
import json

from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import dash.api
import dash.constants
import dash.models
import dash.upload

from utils import k1_helper, request_signer

logger = logging.getLogger(__name__)


# NOTE: keep in sync with R1 (https://github.com/Zemanta/r1/blob/master/config/config.go#L69)
TEST_AD_GROUP_IDS = [
    2539,
    2591,  # click capping test in product campaign
]


@csrf_exempt
def click_capping(request):
    try:
        request_signer.verify_wsgi_request(request, settings.R1_API_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid signature.')
        raise Http404

    content_ad_id = int(request.GET.get('creativeId'))
    content_ad = dash.models.ContentAd.objects.filter(
        id=content_ad_id,
        ad_group_id__in=TEST_AD_GROUP_IDS,
    ).select_related('ad_group').get()

    dash.api.update_content_ads_state([content_ad], dash.constants.ContentAdSourceState.INACTIVE, request)

    # TODO: enable if needed
    # content_ad.ad_group.write_history(
    #     'Content ad {} stopped after reaching the click limit.',
    #     system_user=dash.constants.SystemUserType.K1_USER,
    #     action_type=dash.constants.HistoryActionType.CONTENT_AD_STATE_CHANGE
    # )

    k1_helper.update_content_ads(
        content_ad.ad_group.id,
        content_ad.id,
        msg='AdGroupContentAdState.post'
    )

    return JsonResponse({
        "status": 'ok'
    })


@csrf_exempt
def article_upload(request):
    try:
        request_signer.verify_wsgi_request(request, settings.LAMBDA_CONTENT_UPLOAD_SIGN_KEY)
    except request_signer.SignatureError:
        logger.exception('Invalid signature.')
        raise Http404

    articles_data = json.loads(request.body)
    batch_name = 'Article ' + articles_data[0]['label']
    if len(articles_data) > 1:
        batch_name = 'Multiple articles upload'

    # prevent inserting multiple times if calls are repeated
    existing_candidate_labels = dash.models.ContentAdCandidate.objects.filter(
        label__in=[article['label'] for article in articles_data]
    ).values_list('label', flat=True)

    existing_contentad_labels = dash.models.ContentAd.objects.filter(
        label__in=[article['label'] for article in articles_data]
    ).values_list('label', flat=True)

    candidates_data = []
    for article in articles_data:
        if article['label'] in existing_candidate_labels or article['label'] in existing_contentad_labels:
            continue
        candidates_data.append(article)

    if len(candidates_data) < 1:
        return JsonResponse({
            "status": 'ok'
        })

    ad_group = dash.models.AdGroup.objects.get(id=TEST_AD_GROUP_IDS[0])
    batch, candidates = dash.upload.insert_candidates(
        candidates_data, ad_group, batch_name, filename='', auto_save=True)

    return JsonResponse({
        "status": 'ok'
    })
