import logging

import influx

import automation.autopilot
from utils.command_helpers import ExceptionCommand
import utils.slack

logger = logging.getLogger(__name__)

ALERT_MSG = """Autopilot terminated with an exception today ({}). PagerDuty alert might not have been sent. Check <https://sentry.io/zemanta/eins-1/|sentry>."""


class Command(ExceptionCommand):
    help = "Autopilot rearranges daily spend caps and bid CPCs of all active media sources in participating ad groups."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', dest='dry_run', action='store_true',
                            help='Dry run (don\'t update budgets and bids)')
        parser.add_argument('--daily-run', dest='daily_run', action='store_true',
                            help='Designates this as a part of daily job. Warning: This can cause campaigns in '
                                 'landing mode to overspend. Only to be used manually in rare events.')

    @influx.timer('automation.autopilot_plus.run_autopilot_job')
    def handle(self, *args, **options):
        logger.info('Running Ad Group Autopilot.')
        dry_run = options.get('dry_run', False)
        daily_run = options.get('daily_run', False)
        try:
            automation.autopilot.run_autopilot(
                send_mail=not dry_run,
                report_to_influx=not dry_run,
                dry_run=dry_run,
                daily_run=daily_run,
            )
        except Exception as exc:
            if not dry_run:
                utils.slack.publish(
                    ALERT_MSG.format(repr(exc)),
                    msg_type=utils.slack.MESSAGE_TYPE_CRITICAL,
                    username='Autopilot')
            raise
