import logging

from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Monitor blacklisted publishers by checking for publisher statistics in Redshift that should not exist."

    def add_arguments(self, parser):
        parser.add_argument(
            '--blacklisted_before',
            help='Iso formatted date. All pub. blacklist entries after this date will be ignored'
        )

    def handle(self, *args, **options):
        # TODO
        pass
