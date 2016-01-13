import logging

from django.db import connections
from django.conf import settings
from django.core.management.base import BaseCommand

from utils.command_helpers import set_logger_verbosity, ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Drops the database"

    def add_arguments(self, parser):
        parser.add_argument('alias', metavar='DATABASE_ALIAS', nargs=1,
                            help='Alias of the database to drop (key of the database in settings.DATABASES)')
        parser.add_argument('meta', metavar='META', nargs=1,
                            help='Alias of the database from which the drop will be made (key of the database in settings.DATABASES)')
        parser.add_argument('--noinput', dest='interactive', action='store_false', default=True,
                            help='Suppress input prompts, automatically answer YES')

    def handle(self, *args, **options):
        alias = options['alias'][0]
        meta = options['meta'][0]
        interactive = options.get('interactive', True)

        set_logger_verbosity(logger, options)

        confirm = 'no'
        if interactive:
            confirm = raw_input("""You have requested to drop the '%s' database on host '%s'.
This will IRREVERSIBLY DESTROY the database.

Are you sure you want to do this?
    Type the database name to continue, or 'no' to cancel: """ % (settings.DATABASES[alias]['NAME'],
                                                                  settings.DATABASES[alias]['HOST']))
        else:
            confirm = settings.DATABASES[alias]['NAME']

        if settings.DATABASES[alias]['NAME'] != confirm:
            self.stdout.write("Drop has been cancelled.\n")

        logger.debug('Connecting to "{}::{}"'.format(meta, settings.DATABASES[meta]['NAME']))

        cursor = connections[meta].cursor()
        logger.debug('Connected successfully. Droping "{}" database.'.format(settings.DATABASES[alias]['NAME']))

        cursor.execute('DROP DATABASE {}'.format(settings.DATABASES[alias]['NAME']))
        cursor.close()

        logger.debug('Database successfully dropped.')
