from dash.features.supply_reports.service import refresh_partnerstats
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    def handle(self, *args, **options):
        logger.info("Refreshing partnerstats")
        refresh_partnerstats()
