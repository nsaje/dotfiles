import datetime

from utils.command_helpers import ExceptionCommand

import reports.refresh_k1


class Command(ExceptionCommand):

    help = "Refreshes k1 daily statements and materialized views"

    def add_arguments(self, parser):
        parser.add_argument('from_date', type=str)

    def handle(self, *args, **options):
        since = datetime.datetime.strptime(options['from_date'], '%Y-%m-%d')

        reports.refresh_k1.refresh_k1_reports(since)
