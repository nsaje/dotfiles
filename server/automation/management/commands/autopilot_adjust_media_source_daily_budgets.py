import logging

import automation.autopilot_budgets
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = "Daily Budgets Auto-Pilot rearranges daily budgets of all active media sources in participating ad groups."

    def handle(self, *args, **options):
        logger.info('Running Daily Budget adjusting Auto-Pilot.')

        automation.autopilot_budgets.adjust_autopilot_ad_groups_budgets()
