import logging

import influx

import automation.autopilot_plus
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = "Autopilot rearranges daily spend caps and bid CPCs of all active media sources in participating ad groups."

    @influx.timer('automation.autopilot_plus.run_autopilot_job')
    def handle(self, *args, **options):
        logger.info('Running Ad Group Autopilot.')

        automation.autopilot_plus.run_autopilot(send_mail=True, report_to_influx=True)
