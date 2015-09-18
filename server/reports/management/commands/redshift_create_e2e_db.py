import logging

from django.core.management.base import BaseCommand

from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)

"""
This command creates a new database for end-to-end tests. The new database is created
from the STATS_E2E_DB_NAME database connection and is created with parameters that
are at this point set for the STATS_DB_NAME database.
"""


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Creating a new Redshift DB')

        # create redshift db
        logger.info('Connecting to Redshift DB {}::{}'.format(settings.STATS_E2E_DB_NAME,
                                                              settings.DATABASES[settings.STATS_E2E_DB_NAME]['NAME']))

        cursor = connections[settings.STATS_E2E_DB_NAME].cursor()
        logger.info('Connected successfully')

        new_db_settings = settings.DATABASES[settings.STATS_DB_NAME]
        logger.info('Creating database {}'.format(new_db_settings['NAME']))
        cursor.execute('CREATE DATABASE {} WITH OWNER {}'.format(new_db_settings['NAME'],
                                                                 new_db_settings['USER']))
        cursor.close()
        logger.info('Database created. Connecting to the newly created database.')
