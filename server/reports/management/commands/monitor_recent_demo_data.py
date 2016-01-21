import dateutil.parser

from optparse import make_option
from django.core.management.base import BaseCommand

import reports.api
import dash.models

from utils.statsd_helper import statsd_gauge
from utils.command_helpers import last_n_days, ExceptionCommand


class Command(ExceptionCommand):
    option_list = BaseCommand.option_list + (
        make_option('--start_date', help='Iso format. Default is three days ago'),
        make_option('--end_date', help='Iso format. Default is today')
    )

    def handle(self, *args, **options):
        if options.get('start_date') is None or options.get('end_date') is None:
            dates = last_n_days(3)
            start_date, end_date = dates[-1], dates[0]
        else:
            start_date = dateutil.parser.parse(options['start_date']).date()
            end_date = dateutil.parser.parse(options['end_date']).date()

        demo_adgroups = dash.models.AdGroup.demo_objects.all()
        demo_totals = reports.api.query(
            start_date=start_date,
            end_date=end_date,
            ad_group=demo_adgroups
        )

        total_impressions = demo_totals.get('impressions') or 0
        total_visits = demo_totals.get('visits') or 0
        total_conversions = sum(x.get('conversions') or 0 for x in demo_totals.get('goals', {}).itervalues())

        statsd_gauge('demo.total_recent_impressions', total_impressions)
        statsd_gauge('demo.total_recent_visits', total_visits)
        statsd_gauge('demo.total_recent_conversions', total_conversions)
