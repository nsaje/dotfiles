import logging

from django.db import connections
from django.conf import settings
from django.core.management.base import BaseCommand

from utils.command_helpers import set_logger_verbosity

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Drops the database"

    def add_arguments(self, parser):
        parser.add_argument('alias', metavar='ALIAS', nargs=1,
                            help='Alias of the database to drop')
        parser.add_argument('meta', metavar='META', nargs=1,
                            help='Alias of the database from which the drop will be made')

    def handle(self, *args, **options):
        alias = options['alias'][0]
        meta = options['meta'][0]
        set_logger_verbosity(logger, options)

        logger.debug('Connecting to "{}::{}"'.format(meta, settings.DATABASES[meta]['NAME']))

        cursor = connections[meta].cursor()
        logger.debug('Connected successfully. Droping "{}" database.'.format(settings.DATABASES[alias]['NAME']))

        cursor.execute('DROP DATABASE {}'.format(settings.DATABASES[alias]['NAME']))
        cursor.close()

        logger.debug('Database successfully dropped.')
