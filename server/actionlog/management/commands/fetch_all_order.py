import logging

from optparse import make_option
from django.core.management.base import BaseCommand

from utils.command_helpers import last_n_days, parse_date

from actionlog import api

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--date', help='Iso format. Default is last 3 days.'),
    )

    def handle(self, *args, **options):
        selected_date = parse_date(options)

        if selected_date:
            dates = [selected_date]
        else:
            dates = last_n_days(3)

        logger.info('Fetching status and reports for dates: %s for all ad groups.', dates)
        api.init_fetch_all_order(dates)
