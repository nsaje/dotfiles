import logging

from django.core.management.base import BaseCommand

import automation.autopilot

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('Running bid CPC adjusting Auto-Pilot.')

        automation.autopilot.adjust_autopilot_media_sources_bid_cpcs()
