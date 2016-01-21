import datetime
import logging

from django.core.management import BaseCommand

import dash.models
from utils import statsd_helper
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        logger.info('Conversion pixel monitoring')

        last_sync_dts = dash.models.ConversionPixel.objects.\
            filter(archived=False).values_list('last_sync_dt', flat=True)
        min_last_sync_dt = min(last_sync_dt for last_sync_dt in last_sync_dts if last_sync_dt is not None)
        hours_since = (datetime.datetime.utcnow() - min_last_sync_dt).total_seconds() // 3600
        num_unsynced = len([last_sync_dt for last_sync_dt in last_sync_dts if last_sync_dt is None])

        statsd_helper.statsd_gauge('convapi.conversion_pixels.hours_since_last_sync', hours_since)
        statsd_helper.statsd_gauge('convapi.conversion_pixels.num_cp_not_synced', num_unsynced)
