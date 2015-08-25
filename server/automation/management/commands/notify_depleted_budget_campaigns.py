import logging
from django.core.management.base import BaseCommand
from automation import budgetdepletion
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('Notifying depleted budget campaigns.')
        campaigns = budgetdepletion._get_active_campaigns()
        available_budgets = budgetdepletion._get_available_budgets(campaigns)
        yesterdays_spends = budgetdepletion._get_yesterdays_spends(campaigns)

        for camp in campaigns:
            if budgetdepletion.budget_is_depleting(available_budgets.get(getattr(camp, 'pk')), yesterdays_spends.get(getattr(camp, 'pk'))) and \
                    not budgetdepletion.manager_has_been_notified(camp):
                budgetdepletion.notify_campaign_with_depleting_budget(camp, available_budgets.get(getattr(camp, 'pk')), yesterdays_spends.get(getattr(camp, 'pk')))
