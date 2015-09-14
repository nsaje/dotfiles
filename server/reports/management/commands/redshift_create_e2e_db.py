import os
import logging

from django.core.management.base import BaseCommand

from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)

"""
This command creates a new database for end-to-end tests. The new database is created
from the STATS_E2E_DB_NAME database connection and is created with parameters that
are set for the STATS_DB_NAME database.

If the new database is set to be owned by some other user than the STATS_E2E_DB_NAME database,
then the STATS_E2E_DB_NAME user needs to have the "createuser" privilege.
"""


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Creating a new Redshift DB')

        migrations_dir = os.path.join(os.path.dirname(__file__), '../../migrations/redshift')

        # sort migrations alphabetically
        migration_files = sorted(os.listdir(migrations_dir))
        logger.info('Found {} migrations in {}'.format(len(migration_files), migrations_dir))

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

        cursor = connections[settings.STATS_DB_NAME].cursor()

        logger.info('Applying migrations')
        for i, mf in enumerate(migration_files):
            with open(os.path.join(migrations_dir, mf), 'r') as f:
                logger.info('Applying migration {}/{} {}'.format(i, len(migration_files), mf))
                cursor.execute(f.read())

        cursor.close()
        logger.info('New database created and initialized')
