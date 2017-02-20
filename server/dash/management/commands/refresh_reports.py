import sys
import logging
import datetime

from dateutil import rrule
from optparse import make_option
from utils.command_helpers import parse_id_list, parse_date
from django.core.management.base import BaseCommand

from reports import refresh
from dash import models
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    option_list = BaseCommand.option_list + (
        make_option('--campaigns', help='Comma separated list of campaign ids.'),
        make_option('--from', help='Date from iso format'),
        make_option('--to', help='Date to iso format'),
        make_option('--verbose', help='Write out as much information as possible.', action='store_true'),
    )

    def handle(self, *args, **options):
        campaign_ids = parse_id_list(options, 'campaigns') if options['campaigns'] is not None else []
        if not campaign_ids:
            logging.exception('No campaign specified. Specify at least one campaign.')
            sys.exit(1)

        today = datetime.date.today()
        date_from = parse_date(options, 'from') or today
        date_to = parse_date(options, 'to') or today

        logger.info('Refreshing reports from {} to {} for selected campaings.'.format(date_from, date_to))

        verbose = bool(options.get('verbose', False))

        nr_days = int((date_to - date_from).days)
        daterange = rrule.rrule(rrule.DAILY, dtstart=date_from, until=date_to)
        for i, cid in enumerate(campaign_ids):
            for j, report_date in enumerate(daterange):
                if verbose:
                    logger.info('Refreshing {i}/{n}({day}/{nr_day})\t{cid}\t{date}\t'.format(
                        i=i,
                        n=len(campaign_ids),
                        day=j + 1,
                        nr_day=nr_days,
                        cid=cid,
                        date=report_date.date()
                    ))

                refresh.refresh_contentadstats(
                    report_date,
                    models.Campaign.objects.get(id=cid)
                )
