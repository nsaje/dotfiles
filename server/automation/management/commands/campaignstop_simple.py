import logging
import influx


from automation import budgetdepletion
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    @influx.timer('campaignstop.job_run', job='simple')
    def handle(self, *args, **options):
        logger.info('Start: Stopping and notifying depleted budget campaigns.')
        budgetdepletion.stop_and_notify_depleted_budget_campaigns()
        logger.info('Finish: Stopping and notifying depleted budget campaigns.')

        logger.info('Start: Notifying campaigns with depleting budget.')
        budgetdepletion.notify_depleting_budget_campaigns()
        logger.info('Finish: Notifying campaigns with depleting budget.')
