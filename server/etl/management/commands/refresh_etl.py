import datetime

import structlog
from analytics import monitor
from etl import materialize
from etl import refresh
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):

    help = "Refreshes daily statements and materialized views"

    def add_arguments(self, parser):
        parser.add_argument("from", type=str)
        parser.add_argument(
            "to",
            type=str,
            default=None,
            nargs="?",
            help="Limit date range - expect daily statements to be reprocessed already.",
        )
        parser.add_argument("--account_id", type=int)
        parser.add_argument("--skip-daily-statements", action="store_true")
        parser.add_argument("--dump-and-abort", type=str)

    def handle(self, *args, **options):
        err = []
        since = None

        skip_daily_statements = options.get("skip_daily_statements") or False

        dump_and_abort = options.get("dump_and_abort")
        if dump_and_abort:
            if not any(mv.TABLE_NAME == dump_and_abort for mv in materialize.MATERIALIZED_VIEWS):
                raise Exception("dump-and-abort should specify a valid table name to dump")

        try:
            since = datetime.datetime.strptime(options["from"], "%Y-%m-%d")
        except Exception as e:
            err.append(e)

            try:
                delta = int(options["from"])
                since = datetime.datetime.today() - datetime.timedelta(days=delta)
            except Exception as e:
                err.append(e)
        to = None
        if options["to"]:
            to = datetime.datetime.strptime(options["to"], "%Y-%m-%d")

        if since is None:
            logger.error(err)
            return
        try:
            refresh.refresh(
                since,
                options.get("account_id"),
                skip_daily_statements=skip_daily_statements,
                dump_and_abort=dump_and_abort,
                update_to=to,
            )
        finally:
            monitor.audit_spend_integrity(None)
