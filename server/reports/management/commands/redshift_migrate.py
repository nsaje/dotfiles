import os
import sys
import logging

from django.core.management.base import BaseCommand

from utils.command_helpers import set_logger_verbosity
from reports import redshift

logger = logging.getLogger(__name__)


def migrate_db(start_index=0):
    logger.info('Migrating Amazon Redshift database')

    migration_files = _get_migrations(start_index)

    cursor = redshift.get_cursor()

    logger.info('Applying migrations')
    try:
        for i, mf in enumerate(migration_files):
            with open(mf, 'r') as f:
                logger.info('Applying migration {} {}/{} {}'.format(start_index + i, i + 1, len(migration_files), mf))
                cursor.execute(f.read(), [])
    except Exception as e:
        logger.exception(e)
    finally:
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

    def add_arguments(self, parser):
        parser.add_argument('--list', help='Lists all of the available migrations', action='store_true')
        parser.add_argument('--start', help='0-based migration index with which migrate/list is started', type=int),
        parser.add_argument('--sql', help='Show sql contents of migrations when listing migrations',
                            action='store_true'),

    def handle(self, *args, **options):
        try:
            is_list_action = bool(options.get('list', False))
            show_sql = bool(options.get('sql', False))
            start_index = int(options.get('start', 0)) if options['start'] is not None else 0
        except:
            logging.exception("Failed parsing command line arguments")
            sys.exit(1)

        set_logger_verbosity(logger, options)

        if is_list_action:
            list_migrations(start_index, show_sql)
        else:
            migrate_db(start_index)
