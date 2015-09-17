import logging

from django.core.management.base import BaseCommand

from automation import budgetdepletion

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('Notifying depleted budget campaigns.')

        budgetdepletion.notify_depleted_budget_campaigns()
