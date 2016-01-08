import logging

from optparse import make_option
from django.core.management.base import BaseCommand

from utils.command_helpers import last_n_days, parse_date, ExceptionCommand

import reports.demo


logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    option_list = BaseCommand.option_list + (
        make_option('--date', help='Iso format. Default is last 3 days.'),
    )

    def handle(self, *args, **options):
        selected_date = parse_date(options)

        if selected_date:
            start_date, end_date = selected_date, selected_date
        else:
            dates = last_n_days(3)
            start_date, end_date = dates[-1], dates[0]

        logger.info('Refreshing demo stats for dates %s to %s' % (start_date, end_date))

        reports.demo.refresh_demo_data(start_date, end_date)

        logger.info('Successfully refreshed demo stats for dates %s to %s' % (start_date, end_date))
