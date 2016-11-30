import datetime
import logging

from utils.command_helpers import ExceptionCommand

from etl import refresh_k1

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Refreshes k1 daily statements and materialized views"

    def add_arguments(self, parser):
        parser.add_argument('from', type=str)
        parser.add_argument('--account_id', type=int)

    def handle(self, *args, **options):
        err = []
        since = None

        try:
            since = datetime.datetime.strptime(options['from'], '%Y-%m-%d')
        except Exception as e:
            err.append(e)

            try:
                delta = int(options['from'])
                since = datetime.datetime.today() - datetime.timedelta(days=delta)
            except Exception as e:
                err.append(e)

        if since is None:
            logger.error(err)
            return

        refresh_k1.refresh_k1_reports(since, options.get('account_id'))
