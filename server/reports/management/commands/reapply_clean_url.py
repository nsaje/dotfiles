import logging

from django.core.management.base import BaseCommand

import reports.api as api

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Running apply_clean_url command.')
        api.reapply_clean_url()
