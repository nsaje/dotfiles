import os
import sys
import logging

from optparse import make_option

from django.core.management.base import BaseCommand

from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)


def migrate_db(start_index=0):
    logger.info('Migrating Amazon Redshift database')

    migration_files = _get_migrations(start_index)

    cursor = connections[settings.STATS_DB_NAME].cursor()

    logger.info('Applying migrations')
    for i, mf in enumerate(migration_files):
        with open(mf, 'r') as f:
            logger.info('Applying migration {} {}/{} {}'.format(start_index + i, i + 1, len(migration_files), mf))
            cursor.execute(f.read())

    cursor.close()
    logger.info('Done, database migrated.')


def list_migrations(start_index=0, show_sql=False):
    migration_files = _get_migrations(start_index)

    for i, mf in enumerate(migration_files):
        logger.info('Migration {} {}/{} {}'.format(start_index + i, i + 1, len(migration_files), mf))

        if show_sql:
            with open(mf, 'r') as f:
                logger.info(f.read())


def _get_migrations(start_index=0):
    migrations_dir = os.path.join(os.path.dirname(__file__), '../../migrations/redshift')

    # sort migrations alphabetically
    migration_files = sorted(os.listdir(migrations_dir))
    migration_files = migration_files[start_index:]
    migration_files = [os.path.join(migrations_dir, mf) for mf in migration_files]

    logger.info('Found {} migrations in {}'.format(len(migration_files), migrations_dir))

    return migration_files


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--list', help='Lists all of the availalbe migrations', action='store_true'),
        make_option('--start', help='Initial migration index', type="int"),
        make_option('--sql', help='Show sql contents of migrations when listing migrations', action='store_true'),
    )

    def handle(self, *args, **options):
        try:
            is_list_action = bool(options.get('list', False))
            show_sql = bool(options.get('sql', False))
            start_index = int(options.get('start', 0)) if options['start'] is not None else 0
        except:
            logging.exception("Failed parsing command line arguments")
            sys.exit(1)

        if is_list_action:
            list_migrations(start_index, show_sql)
        else:
            migrate_db(start_index)
