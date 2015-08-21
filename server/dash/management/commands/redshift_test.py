import logging

from django.core.management.base import BaseCommand
from django.db import connections

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Testing Redshift connection')

        cursor = connections['redshift'].cursor()
        print cursor
