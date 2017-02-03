import logging
import sys
import json

import boto3
import dateutil

from django.conf import settings

import dash.models
from integrations.bizwire.internal import helpers, config
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = """Start lambdas to process businesswire articles for given parameters.
    Usage: ./manage.py bizwire_process_articles [options]

    Available options:
      --date - date for which to import articles in isoformat
      --key - article s3 key
      --missing - find and reprocess missing articles
    """

    def add_arguments(self, parser):
        parser.add_argument('--key', dest='key', nargs=1, type=str)
        parser.add_argument('--date', dest='date', nargs=1, type=str)
        parser.add_argument('--missing', dest='missing', nargs=1, type=bool)
        parser.add_argument('--purge-candidates', dest='--purge-candidates', nargs=1, type=bool)

    def handle(self, *args, **options):
        date = options.get('date')
        key = options.get('key')
        missing = options.get('missing')

        if key:
            self.invoke_lambdas(key)
            return

        if date:
            date = dateutil.parser.parse(date[0]).date()
            keys = helpers.get_s3_keys(date=date)
            self.invoke_lambdas(keys)
            return

        if missing:
            keys = helpers.get_s3_keys(date=date)
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

            logger.info('Skipping {} keys - candidates exist'.format(len(candidate_labels)))
            to_reprocess = to_reprocess - candidate_labels
            reprocess_keys = [labels_keys[label] for label in to_reprocess]
            self.invoke_lambdas(reprocess_keys)
            return

        sys.stderr.write('Specify what to reprocess.')
        sys.exit(1)

    def invoke_lambdas(self, keys):
        lambda_client = boto3.client('lambda', region_name=settings.LAMBDA_REGION)
        for key in keys:
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

            sys.stdout.write('Invoking lambda for key: {}'.format(key))
            lambda_client.invoke(
                FunctionName='z1-businesswire-articles',
                InvocationType='Event',  # async
                Payload=json.dumps(payload)
            )
