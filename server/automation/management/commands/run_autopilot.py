import structlog

import automation.autopilot
import utils.slack
from utils import metrics_compat
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)

ALERT_MSG = """Autopilot terminated with an exception today ({}). PagerDuty alert might not have been sent. Check <https://sentry.io/zemanta/eins-1/|sentry>."""


class Command(Z1Command):
    help = "Autopilot rearranges daily spend caps and bid CPCs of all active media sources in participating ad groups."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", dest="dry_run", action="store_true", help="Dry run (don't update budgets and bids)"
        )
        parser.add_argument(
            "--daily-run",
            dest="daily_run",
            action="store_true",
            help="Designates this as a part of daily job. Warning: This can cause campaigns in "
            "landing mode to overspend. Only to be used manually in rare events.",
        )

    @metrics_compat.timer("automation.autopilot_plus.run_autopilot_job")
    def handle(self, *args, **options):
        logger.info("Running Ad Group Autopilot.")
        dry_run = options.get("dry_run", False)
        daily_run = options.get("daily_run", False)
        try:
            automation.autopilot.run_autopilot(report_to_influx=not dry_run, dry_run=dry_run, daily_run=daily_run)
        except Exception as exc:
            if not dry_run:
                utils.slack.publish(
                    ALERT_MSG.format(repr(exc)),
                    msg_type=utils.slack.MESSAGE_TYPE_CRITICAL,
                    username=utils.slack.USER_AUTOPILOT,
                )
            raise
