import logging
from optparse import make_option

import sys

import datetime
from django.core.management import BaseCommand

from reports import exc
import reports.refresh
from utils import command_helpers
from utils.command_helpers import ExceptionCommand


logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    option_list = BaseCommand.option_list + (
        make_option('-s', '--start-date', help='Start date for the publishers import', dest='start_date'),
        make_option('-e', '--end-date', help='End date for the publishers import', dest='end_date')
    )

    def handle(self, *args, **options):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)

        try:
            start_date = command_helpers.parse_date(options, field_name='start_date', default=yesterday)
            end_date = command_helpers.parse_date(options, field_name='end_date', default=yesterday)
        except:
            logger.info('Failed parsing command line arguments')
            sys.exit(1)

        logger.info('Updating publishers for dates: start_date=%s, end_date=%s', start_date, end_date)

        while start_date <= end_date:
            logger.info('Updating for date: %s', start_date)

            try:
                reports.refresh.refresh_publishers_data(start_date)
            except exc.S3FileNotFoundError:
                logger.info('Not successful... File not found. Continuing ...')

            start_date = start_date + datetime.timedelta(days=1)
