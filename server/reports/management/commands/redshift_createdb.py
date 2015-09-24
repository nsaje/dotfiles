import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.db.utils import ProgrammingError

from utils.command_helpers import set_logger_verbosity

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Creates an Amazon Redshift database."

    def add_arguments(self, parser):
        parser.add_argument('alias', metavar='ALIAS', nargs=1, help='Alias of the database to create')
        parser.add_argument('meta', metavar='META', nargs=1,
                            help='Alias of the database from which the drop will be made')

    def handle(self, *args, **options):
        alias = options['alias'][0]
        meta = options['meta'][0]
        set_logger_verbosity(logger, options)

        logger.setLevel(logging.DEBUG)
        alias_db = settings.DATABASES[alias]
        meta_db = settings.DATABASES[meta]

        logger.debug('Creating "{}" Redshift database'.format(alias_db['NAME']))
        logger.debug('Connecting to "{}::{}"'.format(meta, meta_db['NAME']))

        cursor = connections[meta].cursor()
        logger.debug('Connected successfully')

        try:
            cursor.execute('CREATE DATABASE {} WITH OWNER {}'.format(alias_db['NAME'], alias_db['USER']))
        except ProgrammingError as e:
            logger.error('Cannot create database', e)
        else:
            logger.debug('Database created')
        finally:
            cursor.close()
