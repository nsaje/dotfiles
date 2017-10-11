import logging

from dash.features.ga import refresh_mappings
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = 'Refresh the mapping of which customer GA accounts are linked to which of our GA usernames'

    def handle(self, *args, **options):
        refresh_mappings()
