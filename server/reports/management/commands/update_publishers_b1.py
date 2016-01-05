import logging
from optparse import make_option

import sys

import datetime
from django.core.management import BaseCommand
from django.db import transaction

from reports import redshift
from server import settings
from utils import command_helpers
from utils.s3helpers import S3Helper

logger = logging.getLogger(__name__)

PREFIX_PUBLISHERS_FORMAT = 'publishers/{}-{}'
PUBLISHER_S3_URI_FORMAT = 's3://{}/{}/part-00000.lzo'


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-s', '--start-date', help='Start date for the publishers import', dest='start_date'),
        make_option('-e', '--end-date', help='End date for the publishers import', dest='end_date')
    )

    @transaction.atomic(using=settings.STATS_DB_NAME)
    def handle(self, *args, **options):
        try:
            start_date = self._get_start_date(options)
            end_date = self._get_end_date(options)
        except:
            logger.exception('Failed parsing command line arguments')
            sys.exit(1)
        logger.debug('Updating publishers using bidder stats file: start_date=%s, end_date=%s', start_date, end_date)
        publisher_s3_uri = self._get_s3_publisher_uri(start_date, end_date)
        logger.debug('Inserting publisher data from S3 file: %s', publisher_s3_uri)
        redshift.delete_publishers(start_date, end_date)
        redshift.update_publishers(publisher_s3_uri, settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)

    def _get_start_date(self, options):
        start_date = command_helpers.parse_date(options, 'start_date')
        if start_date is None:
            logger.info("No start date was provided. Using yesterday's date as default value.")
            start_date = datetime.date.today() - datetime.timedelta(days=1)
        return start_date

    def _get_end_date(self, options):
        end_date = command_helpers.parse_date(options, 'end_date')
        if end_date is None:
            logger.info("No end date was provided. Using yesterday's date as default value.")
            end_date = datetime.date.today() - datetime.timedelta(days=1)
        return end_date

    def _get_s3_publisher_uri(self, start_date, end_date):
        bucket_name = settings.S3_BUCKET_STATS
        bucket_b1_eventlog_sync = S3Helper(bucket_name=bucket_name)
        prefix_publishers = PREFIX_PUBLISHERS_FORMAT.format(start_date.isoformat(), end_date.isoformat())
        publishers = bucket_b1_eventlog_sync.list(prefix_publishers)
        latest_publisher = max(publishers, key=self._extract_timestamp)
        publisher_s3_uri = PUBLISHER_S3_URI_FORMAT.format(bucket_name, latest_publisher.name)
        return publisher_s3_uri

    def _extract_timestamp(self, publisher):
        start = publisher.name.find('--') + 2
        return publisher.name[start:]
