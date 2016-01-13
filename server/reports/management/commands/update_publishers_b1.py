import logging
from optparse import make_option

import sys

import datetime
from django.core.management import BaseCommand
from django.db import transaction

import reports.refresh
from server import settings
from utils import command_helpers
from utils.command_helpers import ExceptionCommand


logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    option_list = BaseCommand.option_list + (
        make_option('-s', '--start-date', help='Start date for the publishers import', dest='start_date'),
        make_option('-e', '--end-date', help='End date for the publishers import', dest='end_date')
    )

    def handle(self, *args, **options):
        try:
            start_date = self._get_start_date(options)
            end_date = self._get_end_date(options)
        except:
            logger.exception('Failed parsing command line arguments')
            sys.exit(1)

        logger.debug('Updating publishers using bidder stats file: start_date=%s, end_date=%s', start_date, end_date)

        while start_date <= end_date:
            logger.info('Updating for date: %s', start_date)
            reports.refresh.refresh_b1_publishers_data(start_date)
            start_date = start_date + datetime.timedelta(days=1)

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
