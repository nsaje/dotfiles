import datetime
import json
import logging

import boto3
from django.conf import settings

from integrations.bizwire import config
from integrations.bizwire.internal import helpers
import dash.models
from utils import dates_helper

logger = logging.getLogger(__name__)

FIND_MISSING_NUM_DAYS = 7


def get_missing_keys(num_days=FIND_MISSING_NUM_DAYS):
    dates = [dates_helper.utc_today() - datetime.timedelta(days=i) for i in reversed(range(num_days))]
    keys = [k for k in helpers.get_s3_keys_for_dates(dates)
            if helpers.get_s3_key_dt(k).date() >= config.START_DATE]
    labels_keys = {
        helpers.get_s3_key_label(key): key
        for key in keys
    }

    content_ad_labels = set(
        dash.models.ContentAd.objects.filter(
            ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
            label__in=labels_keys.keys(),
        ).values_list('label', flat=True)
    )

    to_reprocess = set([
        l for l in labels_keys.keys() if l not in content_ad_labels
    ])
    candidate_labels = set(
        dash.models.ContentAd.objects.filter(
            ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
            label__in=to_reprocess,
        ).values_list('label', flat=True)
    )

    to_reprocess = to_reprocess - candidate_labels
    reprocess_keys = [labels_keys[label] for label in to_reprocess]
    return reprocess_keys


def purge_candidates(keys):
    labels = [helpers.get_s3_key_label(key) for key in keys]
    candidates = dash.models.ContentAdCandidate.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
        label__in=labels,
    )
    return candidates.delete()[0]


def invoke_lambdas(keys):
    lambda_client = boto3.client('lambda', region_name=settings.LAMBDA_REGION)
    for key in keys:
        logger.info('Reprocessing %s.', key)
        payload = {
            'Records': [{
                's3': {
                    'bucket': {
                        'name': 'businesswire-articles',
                    },
                    'object': {
                        'key': key
                    },
                },
            }]
        }

        lambda_client.invoke(
            FunctionName='z1-businesswire-articles',
            InvocationType='Event',  # async
            Payload=json.dumps(payload)
        )
