import utils.pagerduty_helper as pgdh
from dash.features.supply_reports.service import send_supply_reports
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    @pgdh.catch_and_report_exception(pgdh.PagerDutyEventType.PRODOPS)
    def handle(self, *args, **options):
        logger.info("Sending Supply Reports")
        send_supply_reports()
