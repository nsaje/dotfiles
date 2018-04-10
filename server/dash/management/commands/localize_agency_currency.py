from django.db.models import Q

import core.multicurrency
from etl import daily_statements_k1

import dash.constants
import dash.models
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):

    help = "Deletes user and all references permanently from db"

    def add_arguments(self, parser):
        parser.add_argument('agency_id', type=int)

    def handle(self, *args, **options):
        agency = dash.models.Agency.objects.get(id=options['agency_id'])
        currency = dash.constants.Currency.EUR
        if not self._confirm_delete(agency, currency):
            return

        credits = dash.models.CreditLineItem.objects.filter(Q(agency=agency) | Q(account__agency=agency))
        self._update_currency_on_credits(credits, currency)
        self._adjust_budget_amounts(credits, currency)
        self._reprocess_daily_statements(agency)

    def _confirm_delete(self, agency, currency):
        result = input(
            'You are about to localize agency %s (%s) to use %s. '
            'Do you want to continue? [y/N]' % (agency.name, agency.id, currency))
        return len(result) > 0 and result[0].lower() == "y"

    def _update_currency_on_credits(self, credits, currency):
        for credit in credits:
            credit.currency = currency
            credit.save()

    def _adjust_budget_amounts(credits, currency):
        budgets = dash.models.BudgetLineItem.objects.filter(credit__in=credits)
        for budget in budgets:
            exchange_rate_date = budget.created_dt.date()
            exchange_rate = core.multicurrency.get_exchange_rate(exchange_rate_date, currency)
            budget.amount = int(budget.amount * exchange_rate)
            budget.freed_cc = int(budget.freed_cc * exchange_rate)
            budget.save()

    def _reprocess_daily_statements(agency):
        for account in agency.account_set.all():
            budgets = dash.models.BudgetLineItem.objects.filter(campaign__account=account)
            date_since = min(budget.start_date for budget in budgets)
            daily_statements_k1.reprocess_daily_statements(
                date_since, account_id=account.id)
