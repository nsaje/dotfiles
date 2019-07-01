import logging

from dash.features.ga import refresh_mappings
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)


class Command(Z1Command):
    help = "Refresh the mapping of which customer GA accounts are linked to which of our GA usernames"

    def handle(self, *args, **options):
        refresh_mappings()
