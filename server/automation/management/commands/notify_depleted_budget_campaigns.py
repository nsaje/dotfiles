import logging

from django.core.management.base import BaseCommand

from automation import budgetdepletion

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('Stopping and notifying depleted budget campaigns.')
        budgetdepletion.stop_and_notify_depleted_budget_campaigns()

        logger.info('Notifying campaigns with depleting budget.')
        budgetdepletion.notify_depleting_budget_campaigns()
