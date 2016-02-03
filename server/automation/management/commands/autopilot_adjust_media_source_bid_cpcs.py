import logging

import automation.autopilot
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = "CPC Auto-Pilot adjusts bid CPCs of all participating media sources."

    def handle(self, *args, **options):
        logger.info('Running bid CPC adjusting Auto-Pilot.')

        automation.autopilot.adjust_autopilot_media_sources_bid_cpcs()
