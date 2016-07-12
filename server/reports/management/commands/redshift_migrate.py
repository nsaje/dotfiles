import os
import sys
import logging

from utils.command_helpers import set_logger_verbosity, ExceptionCommand
from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)


def migrate_db(start_index=0, app_label=None):
    logger.info('Migrating Amazon Redshift database')

    migration_files = _get_migrations(start_index, app_label)

    with connections[settings.STATS_DB_NAME].cursor() as cursor:
        logger.info('Applying migrations')
        for i, mf in enumerate(migration_files):
            with open(mf, 'r') as f:
                logger.info('Applying migration {} {}/{} {}'.format(start_index + i, i + 1, len(migration_files), mf))
                cursor.execute(f.read(), [])

        logger.info('Done, database migrated.')


def list_migrations(start_index=0, app_label=None, show_sql=False):
    migration_files = _get_migrations(start_index, app_label)

    for i, mf in enumerate(migration_files):
        logger.info('Migration {} {}/{} {}'.format(start_index + i, i + 1, len(migration_files), mf))

        if show_sql:
            with open(mf, 'r') as f:
                logger.info(f.read())


def _select_migrations_after_index(migration_files, start_index):
    if not start_index:
        return migration_files

    selected = []
    for mf in migration_files:
        try:
            index = int(mf[:4])
        except ValueError as e:
            logger.exception("Migration file not in the right format")

        if index >= start_index:
            selected.append(mf)
    return selected


def _get_migrations(start_index=0, app_label=None):
    migration_files = []

    if not app_label or app_label == 'reports':
        migrations_dir = os.path.join(os.path.dirname(__file__), '../../migrations/redshift')

        # sort migrations alphabetically
        migration_files = sorted(os.listdir(migrations_dir))
        migration_files = _select_migrations_after_index(migration_files, start_index)
        migration_files = [os.path.join(migrations_dir, mf) for mf in migration_files]

    if not app_label or app_label == 'etl':
        migrations_dir = os.path.join(os.path.dirname(__file__), '../../../etl/migrations/redshift')
        migration_files_etl = sorted(os.listdir(migrations_dir))
        migration_files_etl = _select_migrations_after_index(migration_files_etl, start_index)
        migration_files_etl = [os.path.join(migrations_dir, mf) for mf in migration_files_etl]

        migration_files += migration_files_etl

    logger.info('Found {} migrations in {}'.format(len(migration_files), migrations_dir))

    return migration_files


class Command(ExceptionCommand):

    def add_arguments(self, parser):
        parser.add_argument('--list', help='Lists all of the available migrations', action='store_true')
        parser.add_argument('--start', help='0-based migration index with which migrate/list is started', type=int),
        parser.add_argument('--app', help='App label of an application to synchronize the state.', type=str),
        parser.add_argument('--sql', help='Show sql contents of migrations when listing migrations',
                            action='store_true'),

    def handle(self, *args, **options):
        try:
            is_list_action = bool(options.get('list', False))
            show_sql = bool(options.get('sql', False))
            start_index = int(options.get('start', 0)) if options['start'] is not None else 0
            app_label = str(options.get('app', ''))
        except:
            logging.exception("Failed parsing command line arguments")
            sys.exit(1)

        set_logger_verbosity(logger, options)

        if is_list_action:
            list_migrations(start_index, app_label, show_sql)
        else:
            migrate_db(start_index, app_label)
