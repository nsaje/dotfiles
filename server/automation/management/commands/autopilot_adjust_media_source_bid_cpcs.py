import logging

from django.core.management.base import BaseCommand

import automation.autopilot
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        logger.info('Running bid CPC adjusting Auto-Pilot.')

        automation.autopilot.adjust_autopilot_media_sources_bid_cpcs()
