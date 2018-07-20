import logging

from dash.features.bluekai.service import maintenance
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = "Refresh and cross check BlueKai categories"

    def add_arguments(self, parser):
        parser.add_argument("category_id", type=int)

    def handle(self, *args, **options):
        maintenance.add_category_to_audience(options["category_id"])
