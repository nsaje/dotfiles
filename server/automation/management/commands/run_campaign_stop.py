import logging

from automation import campaign_stop
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        # should happen in this order
        campaign_stop.update_campaigns_in_landing()
        campaign_stop.switch_low_budget_campaigns_to_landing_mode()
