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
        make_option('--verbose', help='Write out as much information as possible.', action='store_true'),
        make_option('--to', help='Date to YYYYMMDD'),
    )

    def handle(self, *args, **options):
        logger.info('Inserting stats into Redshift')

        adgroup_ids = parse_id_list(options, 'adgroups') if options['adgroups'] is not None else []
        date_from = datetime.datetime.strptime(options['from'], '%Y%m%d') if options['from'] else None
        date_to = datetime.datetime.strptime(options['to'], '%Y%m%d') if options['to'] else None
        verbose = bool(options.get('verbose', False))

        if not all([adgroup_ids, date_from, date_to]):
            logging.exception("Failed parsing command line arguments")
            sys.exit(1)

        n = len(adgroup_ids)
        n_days = int((date_to - date_from).days)
        for i, agid in enumerate(adgroup_ids):
            for days in range(n_days):
                day = date_from + datetime.timedelta(days)
                if verbose:
                    print 'Refreshing {i}/{n}({i_day}/{n_day})\t{agid}\t{date}'.format(
                        i=i,
                        n=n,
                        i_day=days,
                        n_day=n_days,
                        agid=agid,
                        date=day
                    ),

                refresh.refresh_contentadstats(
                    day,
                    models.AdGroup.objects.get(id=agid)
                )

                if verbose:
                    print 'DONE'
