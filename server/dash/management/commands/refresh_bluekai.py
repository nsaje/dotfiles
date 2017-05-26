import logging

from dash.features.bluekai.service import maintenance
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        maintenance.refresh_bluekai_categories()
        maintenance.cross_check_audience_categories()
