import logging

from django.core.management.base import BaseCommand

from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.debug('Cleaning up Redshift E2E DB')

        logger.debug('Connecting to Redshift DB {}::{}'.format(settings.STATS_E2E_DB_NAME,
                                                               settings.DATABASES[settings.STATS_E2E_DB_NAME]['NAME']))

        cursor = connections[settings.STATS_E2E_DB_NAME].cursor()
        logger.debug('Connected successfully. Droping the temporary e2e database.')

        cursor.execute('DROP DATABASE {}'.format(settings.DATABASES[settings.STATS_DB_NAME]['NAME']))
        cursor.close()

        logger.debug('Database successfully dropped. All done.')
