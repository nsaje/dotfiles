import logging

import automation.autopilot_plus
from utils.command_helpers import ExceptionCommand
from utils.statsd_helper import statsd_timer

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = "Auto-Pilot rearranges daily budgets and bid CPCs of all active media sources in participating ad groups."

    @statsd_timer('automation.autopilot_plus', 'run_autopilot_job')
    def handle(self, *args, **options):
        logger.info('Running Ad Group Auto-Pilot.')

        automation.autopilot_plus.run_autopilot(send_mail=True, report_to_statsd=True)
