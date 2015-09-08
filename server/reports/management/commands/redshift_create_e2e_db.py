import os
import logging

from django.core.management.base import BaseCommand

from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.debug('Creating a new Redshift DB')

        migrations_dir = os.path.join(os.path.dirname(__file__), '../../migrations/redshift')

        # sort migrations alphabetically
        migration_files = sorted(os.listdir(migrations_dir))
        logger.debug('Found {} migrations in {}'.format(len(migration_files), migrations_dir))

        # create redshift db
        logger.debug('Connecting to Redshift DB {}::{}'.format(settings.STATS_E2E_DB_NAME,
                                                               settings.DATABASES[settings.STATS_E2E_DB_NAME]['NAME']))

        cursor = connections[settings.STATS_E2E_DB_NAME].cursor()
        logger.debug('Connected successfully')

        new_db_settings = settings.DATABASES[settings.STATS_DB_NAME]
        logger.debug('Creating database {}'.format(new_db_settings['NAME']))
        cursor.execute('CREATE DATABASE {} WITH OWNER {}'.format(new_db_settings['NAME'],
                                                                 new_db_settings['USER']))
        cursor.close()
        logger.debug('Database created. Connecting to the newly created database.')

        cursor = connections[settings.STATS_DB_NAME].cursor()

        logger.debug('Applying migrations')
        for i, mf in enumerate(migration_files):
            with open(os.path.join(migrations_dir, mf), 'r') as f:
                logger.debug('Applying migration {}/{} {}'.format(i, len(migration_files), mf))
                cursor.execute(f.read())

        cursor.close()
        logger.debug('New database created and initialized')
