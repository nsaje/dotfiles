from collections import defaultdict
import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

import dash.models
import reports.models
from utils import dates_helper


# TODO: How should we handle canceled account credits and pending campaign budgets?
# Should canceled credit's budgets have spend until the date the credit has been canceled?

def _generate_statement(campaign, date):
    budgets = dash.models.BudgetLineItem.objects.filter(campaign_id=campaign.id,
                                                        start_date__lte=date,
                                                        end_date__gte=date)
    existing_statements = dash.models.BudgetDailyStatement.objects.filter(budget__campaign_id=campaign.id)
    existing_statements.filter(date=date).delete()

    stats = reports.models.ContentAdStats.objects\
                                         .filter(content_ad__ad_group__campaign_id=campaign.id, date=date)\
                                         .aggregate(cost_cc_sum=Sum('cost_cc'), data_cost_cc_sum=Sum('data_cost_cc'))

    per_budget_spend = defaultdict(Decimal)
    for existing_statement in existing_statements:
        per_budget_spend[existing_statement.budget_id] += existing_statement.spend

    total_spend = (Decimal(stats['cost_cc_sum']) / 10000) + (Decimal(stats['data_cost_cc_sum']) / 10000)
    for budget in budgets.order_by('created_dt'):
        attributed_amount = 0
        fee_amount = 0
        if total_spend > 0 and per_budget_spend[budget.id] < budget.amount:
            available_budget = (budget.amount - per_budget_spend[budget.id]) / (1 + budget.credit.license_fee)
            attributed_amount = total_spend
            if total_spend > available_budget:
                attributed_amount = available_budget
            fee_amount = attributed_amount * budget.credit.license_fee

            per_budget_spend[budget.id] += attributed_amount + fee_amount
            total_spend -= attributed_amount

        dash.models.BudgetDailyStatement.objects.create(budget_id=budget.id, date=date,
                                                        spend=attributed_amount + fee_amount)

    if total_spend > 0:
        # TODO: over spend, to be decided what to do
        pass


def _get_dates(campaign):
    budgets = dash.models.BudgetLineItem.objects.filter(campaign_id=campaign.id)
    existing_statements = dash.models.BudgetDailyStatement.objects.filter(budget__campaign_id=campaign.id)

    by_date = defaultdict(dict)
    for existing_statement in existing_statements:
        by_date[existing_statement.date][existing_statement.budget_id] = existing_statement

    from_date = min(budget.start_date for budget in budgets)
    today = dates_helper.utc_datetime_to_local_date(datetime.datetime.utcnow())
    while True:
        found = False
        for budget in budgets:
            if budget.start_date <= from_date and budget.end_date >= from_date and\
               (budget.id not in by_date[from_date] or by_date[from_date][budget.id].dirty):
                found = True

        if found or from_date == today:
            break

        from_date += datetime.timedelta(days=1)

    return [from_date + datetime.timedelta(days=i) for i in range((today - from_date).days + 1)]


@transaction.atomic
def reprocess_daily_statements(campaign):
    dates = _get_dates(campaign)
    for date in dates:
        _generate_statement(campaign, date)
