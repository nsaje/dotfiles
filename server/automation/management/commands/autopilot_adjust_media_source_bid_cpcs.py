import logging

from django.core.management.base import BaseCommand

import automation.autopilot

logger = logging.getLogger(__name__)
from freezegun import freeze_time



class Command(BaseCommand):
    @freeze_time("2015-04-21 14:11:05", tz_offset=-4)
    def handle(self, *args, **options):
        logger.info('Running bid CPC adjusting Auto-Pilot.')

        automation.autopilot.adjust_autopilot_media_sources_bid_cpcs()
