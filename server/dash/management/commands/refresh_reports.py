import sys
import logging
import datetime

from dateutil import rrule
from optparse import make_option
from utils.command_helpers import parse_id_list, parse_date
from django.core.management.base import BaseCommand

from reports import refresh
from dash import models

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--adgroups', help='Comma separated list of adgroup ids.'),
        make_option('--from', help='Date from iso format'),
        make_option('--to', help='Date to iso format'),
        make_option('--verbose', help='Write out as much information as possible.', action='store_true'),
    )

    def handle(self, *args, **options):
        adgroup_ids = parse_id_list(options, 'adgroups') if options['adgroups'] is not None else []
        if not adgroup_ids:
            logging.exception('No ad group specified. Specify at least one ad group.')
            sys.exit(1)

        today = datetime.date.today()
        date_from = parse_date(options, 'from') or today
        date_to = parse_date(options, 'to') or today

        logger.info('Refreshing reports from {} to {} for selected ad groups.'.format(date_from, date_to))

        verbose = bool(options.get('verbose', False))

        nr_days = int((date_to - date_from).days)
        daterange = rrule.rrule(rrule.DAILY, dtstart=date_from, until=date_to)
        for i, agid in enumerate(adgroup_ids):
            for j, report_date in enumerate(daterange):
                if verbose:
                    logger.info('Refreshing {i}/{n}({day}/{nr_day})\t{agid}\t{date}\t'.format(
                        i=i,
                        n=len(adgroup_ids),
                        day=j + 1,
                        nr_day=nr_days,
                        agid=agid,
                        date=report_date.date()
                    ))

                refresh.refresh_contentadstats(
                    report_date,
                    models.AdGroup.objects.get(id=agid)
                )
