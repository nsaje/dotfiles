import logging
import sys
import json

import boto3
import dateutil

from django.conf import settings

from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = """Start lambdas to process businesswire articles for given parameters.
    Usage: ./manage.py bizwire_process_articles [options]

    Available options:
      --date - date for which to import articles in isoformat
      --key - article s3 key
    """

    def add_arguments(self, parser):
        parser.add_argument('--key', dest='key', nargs=1, type=str)
        parser.add_argument('--date', dest='date', nargs=1, type=str)

    def handle(self, *args, **options):
        date = options.get('date')
        key = options.get('key')

        if not key and not date:
            sys.stderr.write('Missing date or key argument')
            sys.exit(1)

        if key:
            self.invoke_lambdas(key)
            return

        date = dateutil.parser.parse(date[0]).date()
        keys = self.get_all_keys(date)
        self.invoke_lambdas(keys)

    def get_all_keys(self, date):
        s3_client = boto3.client('s3')
        keys = []
        prefix = 'uploads/{}/{}/{}'.format(date.year, date.month, date.day)
        for obj in s3_client.list_objects(Bucket='businesswire-articles', Prefix=prefix)['Contents']:
            keys.append(obj['Key'])
        return keys

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

            lambda_client.invoke(
                FunctionName='z1-businesswire-articles',
                InvocationType='Event',  # async
                Payload=json.dumps(payload)
            )
