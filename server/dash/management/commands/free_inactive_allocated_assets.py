import datetime
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

import dash.models
from utils.command_helpers import parse_id_list


class Command(BaseCommand):
    help = 'Free recently inactive budget assets.'
    option_list = BaseCommand.option_list + (
        make_option('--budget-ids', help="Budget line item IDs"),
        make_option('--verbose', action='store_true', default=False, help="Verbose"),
    )

    def handle(self, *args, **options):
        today = datetime.date.today()
        budget_ids = set(parse_id_list(options, 'budget_ids') or [])
        is_verbose = options.get('verbose', False)

        candidate_budgets = dash.models.BudgetLineItem.objects.filter(
            **(budget_ids and dict(pk__in=budget_ids) or dict(
                end_date__lt=today,
                end_date__gte=today - datetime.timedelta(settings.LAST_N_DAY_REPORTS + 1)
            ))
        )

        for budget in candidate_budgets:
            if is_verbose:
                self.stdout.write('Processing {}\n'.format(str(budget)))
            budget.free_inactive_allocated_assets()
            if is_verbose:
                self.stdout.write('Budget has ${} assets freed.\n'.format(
                    budget.freed_cc * dash.models.CC_TO_DEC_MULTIPLIER
                ))
