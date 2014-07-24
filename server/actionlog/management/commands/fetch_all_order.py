import logging

from django.core.management.base import BaseCommand

from actionlog import sync

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Fetching status and reports for all ad groups.')
        sync.GlobalSync().trigger_all()
