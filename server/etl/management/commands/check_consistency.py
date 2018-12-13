import datetime
import logging

from etl import consistency_check
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Refreshes daily statements and materialized views"

    def add_arguments(self, parser):
        parser.add_argument("from", type=str)
        parser.add_argument("to", type=str)

    def handle(self, *args, **options):
        err = []
        since = None

        try:
            since = datetime.datetime.strptime(options["from"], "%Y-%m-%d")
        except Exception as e:
            err.append(e)

            try:
                delta = int(options["from"])
                since = datetime.datetime.today() - datetime.timedelta(days=delta)
            except Exception as e:
                err.append(e)

        if since is None:
            logger.error(err)
            return

        err = []
        to = None

        try:
            to = datetime.datetime.strptime(options["to"], "%Y-%m-%d")
        except Exception as e:
            err.append(e)
            try:
                delta = int(options["to"])
                to = datetime.datetime.today() - datetime.timedelta(days=delta)
            except Exception as e:
                err.append(e)

        if to is None:
            logger.error(err)
            return

        consistency_check.consistency_check(since, to)
