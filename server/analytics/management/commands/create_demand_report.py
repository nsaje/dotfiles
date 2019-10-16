import structlog
from analytics import demand_report
from utils import command_helpers

logger = structlog.get_logger(__name__)


class Command(command_helpers.Z1Command):

    help = "Create demant report and upload it to Big Query"

    def handle(self, *args, **options):
        demand_report.create_report()
