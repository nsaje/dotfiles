import os
import logging

from django.core.management.base import BaseCommand

from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        print 'Preparing new redshift dv'

        migrations_dir = os.path.join(os.path.dirname(__file__), '../../migrations/redshift')
        print 'Looking for migrations in', migrations_dir

        # sort alphabetically
        migration_files = sorted(os.listdir(migrations_dir))
        migration_files = map(lambda fn: os.path.join(migrations_dir, fn), migration_files)

        cursor = connections['stats_e2e_meta'].cursor()
        db_settings = settings.DATABASES[settings.STATS_DB_NAME]
        print 'Creating db {}'.format(db_settings['NAME'])

        # connect and create a table
        cursor.execute('CREATE DATABASE {} WITH OWNER {}'.format(db_settings['NAME'], db_settings['USER']))
        cursor.close()

        cursor = connections[settings.STATS_DB_NAME].cursor()
        print 'Applying {} migrations'.format(len(migration_files))

        for i, mf in enumerate(migration_files):
            print 'Applying migration {} {}/{}'.format(mf, i, len(migration_files))

            with open(mf, 'r') as f:
                cursor.execute(f.read())
                print 'OK ',

            print 'DONE'

        cursor.close()
        print 'ALL DONE'
