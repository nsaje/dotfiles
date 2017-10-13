import logging
import socket

from django.conf import settings
from django.db import connections
from django.utils.text import slugify

from utils.command_helpers import set_logger_verbosity, ExceptionCommand


logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Copies schema and data of the current database into a new database"

    def add_arguments(self, parser):
        parser.add_argument('name', metavar='NAME', nargs=1,
                            type=str, help='New name of the database.')

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)

        src_db_name = settings.DATABASES['default']['NAME']
        src_db_owner = settings.DATABASES['default']['USER']
        new_db_name = options['name'][0]

        with connections['default'].cursor() as cursor:
            self.kill_connections(cursor, src_db_name)
            self.copy_db(cursor, src_db_name, src_db_owner, new_db_name)

    def copy_db(self, cursor, src_db_name, src_db_owner, new_db_name):
        sql = "CREATE DATABASE {} WITH TEMPLATE {} OWNER {}".format(new_db_name, src_db_name, src_db_owner)

        logger.info('Copying database "{}" to "{}"'.format(src_db_name, new_db_name))
        cursor.execute(sql)
        logger.info('Database copied')

        print """
        You can set the following settings in your localsettings.py

        DATABASES['default']['NAME'] = '{}'
        """.format(new_db_name)

    def kill_connections(self, cursor, src_db_name):
        sql = """
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = %(src_db_name)s AND pid <> pg_backend_pid();
        """

        params = {
            'src_db_name': src_db_name,
        }

        logger.info('Killing connections to source database')
        cursor.execute(sql, params)
        logger.info('All connections to source database killed')
