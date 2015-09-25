import os
import logging
import yaml
import collections

from django.utils._os import upath
from django.utils.functional import cached_property
from django.apps import apps
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

from utils.command_helpers import set_logger_verbosity

from reports import redshift


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Loads fixtures into the stats database"

    def add_arguments(self, parser):
        parser.add_argument('fixtures', metavar='FIXTURES', nargs='+',
                            help='A list of fixture labels to load. Separated with spaces.')
        parser.add_argument('--app', action='store', dest='app_label',
                            default=None, help='Only look for fixtures in the specified app.')
        parser.add_argument('--noinput', dest='interactive', action='store_false', default=True,
                            help='Suppress input prompts, automatically answer YES')

    def find_fixtures(self, fixture_name):
        """
        Finds fixtures absolute paths.
        """
        if os.path.isabs(fixture_name):
            fixture_dirs = [os.path.dirname(fixture_name)]
            fixture_name = os.path.basename(fixture_name)
        else:
            fixture_dirs = self.fixture_dirs
            if os.path.sep in os.path.normpath(fixture_name):
                fixture_dirs = [os.path.join(dir_, os.path.dirname(fixture_name))
                                for dir_ in fixture_dirs]
                fixture_name = os.path.basename(fixture_name)

        # TODO: does not handle suffixes, fixture label should always containt ".yaml"
        fixtures_w_paths = []
        for fixture_dir in fixture_dirs:
            path = os.path.join(fixture_dir, fixture_name)
            if os.path.exists(path):
                fixtures_w_paths.append(path)
        return fixtures_w_paths

    def handle(self, *args, **options):
        fixtures = options['fixtures']
        self.app_label = options.get('app_label')
        interactive = options.get('interactive', True)
        set_logger_verbosity(logger, options)

        confirm = 'no'
        if interactive:
            confirm = raw_input("""You have requested to load fixtures into the '%s' database on host '%s'.

Are you sure you want to do this?
    Type the database name to continue, or 'no' to cancel: """ % (settings.DATABASES[settings.STATS_DB_NAME]['NAME'],
                                                                  settings.DATABASES[settings.STATS_DB_NAME]['HOST']))
        else:
            confirm = settings.DATABASES[settings.STATS_DB_NAME]['NAME']

        if confirm != settings.DATABASES[settings.STATS_DB_NAME]['NAME']:
            self.stdout.write("Fixtures loading was cancelled.\n")

        # load data from fixtures
        data = []
        for fixture_name in fixtures:
            for fixture in self.find_fixtures(fixture_name):
                with open(fixture, 'r') as fs:
                    logger.debug('Reading fixtures {}'.format(fixture))
                    data.append(yaml.load(fs))

        # sort data by tables
        sqlfields_by_table = {}
        rows_by_table = collections.defaultdict(list)

        for block_list in data:
            for block in block_list:
                fields = block['fields']
                table = block['table']

                sql_fields = sqlfields_by_table.setdefault(table, fields.keys())

                # append previously undefined fields
                diff = set(fields.keys()) - set(sql_fields)
                for df in diff:
                    sqlfields_by_table[table].append(df)

                sql_fields = sqlfields_by_table[table]

                rows_by_table[table].append([fields.get(k) for k in sql_fields])

        # insert thy data
        cursor = redshift.get_cursor()
        try:
            with transaction.atomic(using=settings.STATS_DB_NAME):
                for table, fields in sqlfields_by_table.items():
                    max_length = len(sqlfields_by_table[table])

                    # append None to max length of row tuples
                    rows = []
                    for row in rows_by_table[table]:
                        row.extend([None] * (max_length - len(row)))
                        rows.append(row)
                    redshift.execute_multi_insert_sql(cursor, table, fields, rows)
        except Exception as e:
            logger.exception(e)
        finally:
            cursor.close()

    @cached_property
    def fixture_dirs(self):
        """
        Return a list of fixture directories.
        The list contains the 'fixtures' subdirectory of each installed
        application, if it exists, the directories in FIXTURE_DIRS, and the
        current directory.

        This is a simplification of
        django/django/core/management/commands/loaddata.py  Command::fixture_dirs
        """

        dirs = []
        fixture_dirs = settings.FIXTURE_DIRS
        for app_config in apps.get_app_configs():
            app_label = app_config.label
            app_dir = os.path.join(app_config.path, 'fixtures')
            if self.app_label and app_label != self.app_label:
                continue
            if os.path.isdir(app_dir):
                dirs.append(app_dir)
        dirs.extend(list(fixture_dirs))
        dirs.append('')
        dirs = [upath(os.path.abspath(os.path.realpath(d))) for d in dirs]
        return dirs
