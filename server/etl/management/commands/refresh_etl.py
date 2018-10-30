import datetime
import logging

from etl import materialize
from etl import refresh
from utils import dates_helper
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Refreshes daily statements and materialized views"

    def add_arguments(self, parser):
        parser.add_argument("from", type=str)
        parser.add_argument("--account_id", type=int)
        parser.add_argument("--skip-vacuum", action="store_true")
        parser.add_argument("--skip-analyze", action="store_true")
        parser.add_argument("--skip-daily-statements", action="store_true")
        parser.add_argument("--dump-and-abort", type=str)

    def handle(self, *args, **options):
        err = []
        since = None

        skip_vacuum = options.get("skip_vacuum") or False
        skip_analyze = options.get("skip_analyze") or False
        skip_daily_statements = options.get("skip_daily_statements") or False

        dump_and_abort = options.get("dump_and_abort")
        if dump_and_abort:
            if not any(mv.TABLE_NAME == dump_and_abort for mv in materialize.MATERIALIZED_VIEWS):
                raise Exception("dump-and-abort should specify a valid table name to dump")

        hour = dates_helper.local_now().hour
        if 0 <= hour <= 8:
            skip_vacuum = True
            skip_analyze = True

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

        refresh.refresh(
            since,
            options.get("account_id"),
            skip_vacuum=skip_vacuum,
            skip_analyze=skip_analyze,
            skip_daily_statements=skip_daily_statements,
            dump_and_abort=dump_and_abort,
        )
