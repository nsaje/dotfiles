import logging
import json
import sys

import boto3
import dateutil

from django.conf import settings

import dash.models
from integrations.bizwire import config
from integrations.bizwire.internal import helpers
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
        parser.add_argument('--missing', dest='missing', action='store_true')
        parser.add_argument('--dry-run', dest='dry_run', action='store_true')
        parser.add_argument('--purge-candidates', dest='purge_candidates', action='store_true')

    def _get_keys_to_reprocess(self, options):
        if options.get('key'):
            return [options['key']]

        date = options.get('date')
        if date:
            date = dateutil.parser.parse(date[0]).date()
            return helpers.get_s3_keys(date=date)

        missing = options.get('missing')
        if missing:
            keys = [k for k in helpers.get_s3_keys(date=date)
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

            if len(candidate_labels):
                logger.info('Candidates for {} missing labels exist. Use --purge-candidates to remove them.')

            to_reprocess = to_reprocess - candidate_labels
            reprocess_keys = [labels_keys[label] for label in to_reprocess]
            return reprocess_keys

        logger.info('Specify what to reprocess.')
        sys.exit(1)

    def handle(self, *args, **options):
        self.dry_run = options.get('dry_run')
        self.purge_candidates = options.get('purge_candidates')

        keys = self._get_keys_to_reprocess(options)
        self._purge_candidates(keys)
        self._invoke_lambdas(keys)

    def _purge_candidates(self, keys):
        if not self.purge_candidates:
            return

        labels = [helpers.get_s3_key_label(key) for key in keys]
        candidates = dash.models.ContentAdCandidate.objects(
            ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
            label__in=labels,
        )

        num_candidates = candidates.count()
        if self.dry_run:
            logger.info('{} candidates would be removed.\n'.format(num_candidates))
            return
        else:
            logger.info('Removing {} candidates.\n'.format(num_candidates))

        candidates.delete()

    def _invoke_lambdas(self, keys):
        if self.dry_run:
            for key in keys:
                logger.info('{} would be reprocessed'.format(key))
            return

        lambda_client = boto3.client('lambda', region_name=settings.LAMBDA_REGION)
        for key in keys:
            logger.info('Reprocessing {}.'.format(key))
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
