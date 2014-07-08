import logging

from django.core.management.base import BaseCommand

from actionlog import api
from actionlog import refresh_orders

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Refreshing actionlog entries.')

        api.cancel_expired_actionlogs()
        refresh_orders.refresh_fetch_all_orders()
