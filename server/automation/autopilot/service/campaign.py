from collections import defaultdict
from decimal import Decimal

from django.db.models import Q

from dash import models
from utils import dates_helper


def calculate_campaigns_daily_budget(campaign=None):
    today = dates_helper.local_today()

    budgets = (
        models.BudgetLineItem.objects.all()
        .filter(Q(campaign__account__agency__isnull=False) & Q(campaign__account__agency__uses_realtime_autopilot=True))
        .filter_active()
        .annotate_spend_data()
        .select_related("campaign")
    )

    if campaign is not None:
        budgets = budgets.filter(campaign=campaign)
    else:
        budgets = budgets.filter(campaign__settings__autopilot=True)

    daily_budgets = defaultdict(Decimal)
    for budget in budgets:
        remaining_days = (budget.end_date - today).days + 1
        budget_daily_part = budget.get_available_etfm_amount() / remaining_days
        daily_budgets[budget.campaign] += budget_daily_part.quantize(Decimal("1."))

    return daily_budgets
