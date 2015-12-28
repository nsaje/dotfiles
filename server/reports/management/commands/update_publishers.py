import logging
from optparse import make_option

import sys

import datetime
from django.core.management import BaseCommand
from django.db import transaction

from reports import redshift
from server import settings
from utils.s3helpers import S3Helper

logger = logging.getLogger(__name__)

PREFIX_PUBLISHERS_FORMAT = 'publishers/{}-{}'


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-s', '--start-date', help='Start date for the publishers import', dest='start_date'),
        make_option('-e', '--end-date', help='End date for the publishers import', dest='end_date')
    )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            start_date = options['start_date']
            end_date = options['end_date']
        except:
            logger.exception('Failed parsing command line arguments')
            sys.exit(1)
        if start_date is None:
            logger.info("No start date was provided. Using yesterday's date by default.")
            start_date = datetime.date.today() - datetime.timedelta(days=1)
        else:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date is None:
            logger.info("No end date was provided. Using yesterday's date by default.")
            end_date = datetime.date.today() - datetime.timedelta(days=1)
        else:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        logger.info('Updating publishers in RedShift: start_date=%s, end_date=%s', str(start_date), str(end_date))
        redshift.delete_publishers(start_date, end_date)
        bucket_name = settings.S3_BUCKET_B1_EVENTLOG_SYNC
        bucket_b1_eventlog_sync = S3Helper(bucket_name=bucket_name)
        prefix_publishers = PREFIX_PUBLISHERS_FORMAT.format(start_date.isoformat(), end_date.isoformat())
        publishers = bucket_b1_eventlog_sync.list(prefix_publishers)
        for publisher in publishers:
            publisher_s3_uri = 's3://{}/{}'.format(bucket_name, publisher.name)
            redshift.update_publishers(publisher_s3_uri, settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
