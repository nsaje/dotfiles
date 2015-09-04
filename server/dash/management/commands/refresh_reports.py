import sys
import logging
import datetime

from optparse import make_option
from utils.command_helpers import parse_id_list
from django.core.management.base import BaseCommand
from reports import refresh
from dash import models

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--adgroups', help='Comma separated list of adgroup ids. If none specified, nothing happens.'),
        make_option('--from', help='Date from YYYYMMDD'),
        make_option('--to', help='Date to YYYYMMDD'),
        make_option('--verbose', help='Write out as much information as possible.', action='store_true'),
    )

    def handle(self, *args, **options):
        logger.info('Refreshing reports')

        adgroup_ids = parse_id_list(options, 'adgroups') if options['adgroups'] is not None else []
        date_from = datetime.datetime.strptime(options['from'], '%Y%m%d') if options['from'] else None
        date_to = datetime.datetime.strptime(options['to'], '%Y%m%d') if options['to'] else None
        verbose = bool(options.get('verbose', False))

        if not all([adgroup_ids, date_from, date_to]):
            logging.exception("Failed parsing command line arguments")
            sys.exit(1)

        nr_days = int((date_to - date_from).days)
        for i, agid in enumerate(adgroup_ids):
            for day in range(nr_days):
                report_date = date_from + datetime.timedelta(day)
                if verbose:
                    print 'Refreshing {i}/{n}({day}/{nr_day})\t{agid}\t{date}\t'.format(
                        i=i,
                        n=len(adgroup_ids),
                        day=day,
                        nr_day=nr_days,
                        agid=agid,
                        date=report_date
                    ),

                refresh.refresh_contentadstats(
                    report_date,
                    models.AdGroup.objects.get(id=agid)
                )

                if verbose:
                    print 'DONE'
