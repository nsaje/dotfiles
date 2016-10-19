import logging
import json

from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from utils import request_signer
import dash.upload
import dash.models

logger = logging.getLogger(__name__)


TEST_AD_GROUP_ID = 2539


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

    ad_group = dash.models.AdGroup.objects.get(id=TEST_AD_GROUP_ID)
    batch, candidates = dash.upload.insert_candidates(
        candidates_data, ad_group, batch_name, filename='', auto_save=True)
    for candidate in candidates:
        dash.upload.invoke_external_validation(candidate, batch)

    return JsonResponse({
        "status": 'ok'
    })
