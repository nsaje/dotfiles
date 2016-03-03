from collections import defaultdict
from decimal import Decimal
import datetime

from dateutil import rrule
from django.db import transaction
from django.db.models import Sum

import dash.models
import reports.models
from utils import dates_helper

CC_TO_NANO = 100000


def _generate_statements(date, campaign):
    budgets = dash.models.BudgetLineItem.objects.filter(campaign_id=campaign.id,
                                                        start_date__lte=date,
                                                        end_date__gte=date)
    existing_statements = reports.models.BudgetDailyStatement.objects.filter(
        date__lte=date,
        budget__campaign_id=campaign.id)
    existing_statements.filter(date=date).delete()

    stats = reports.models.AdGroupStats.objects\
                                       .filter(ad_group__campaign_id=campaign.id, datetime=date)\
                                       .aggregate(cost_cc_sum=Sum('cost_cc'), data_cost_cc_sum=Sum('data_cost_cc'))

    per_budget_spend_nano = defaultdict(lambda: defaultdict(int))
    for existing_statement in existing_statements:
        per_budget_spend_nano[existing_statement.budget_id]['media'] += existing_statement.media_spend_nano
        per_budget_spend_nano[existing_statement.budget_id]['data'] += existing_statement.data_spend_nano
        per_budget_spend_nano[existing_statement.budget_id]['license_fee'] += existing_statement.license_fee_nano

    total_media_nano = (stats['cost_cc_sum'] if stats['cost_cc_sum'] is not None else 0) * CC_TO_NANO
    total_data_nano = (stats['data_cost_cc_sum'] if stats['data_cost_cc_sum'] is not None else 0) * CC_TO_NANO

    for budget in budgets.order_by('created_dt'):
        budget_amount_nano = budget.amount * (10**9)
        attributed_media_nano = 0
        attributed_data_nano = 0
        license_fee_nano = 0

        total_spend_nano = total_media_nano + total_data_nano
        budget_spend_total_nano = per_budget_spend_nano[budget.id]['media'] +\
            per_budget_spend_nano[budget.id]['data'] +\
            per_budget_spend_nano[budget.id]['license_fee']
        if total_spend_nano > 0 and budget_spend_total_nano < budget_amount_nano:
            available_budget_nano = (budget_amount_nano - budget_spend_total_nano) * (1 - budget.credit.license_fee)
            if total_media_nano + total_data_nano > available_budget_nano:
                if total_media_nano >= available_budget_nano:
                    attributed_media_nano = available_budget_nano
                    attributed_data_nano = 0
                else:
                    attributed_media_nano = total_media_nano
                    attributed_data_nano = available_budget_nano - total_media_nano
            else:
                attributed_media_nano = total_media_nano
                attributed_data_nano = total_data_nano

            license_fee_pct_of_total = (1 / (1 - budget.credit.license_fee)) - 1
            license_fee_nano = (attributed_media_nano + attributed_data_nano) * license_fee_pct_of_total

        per_budget_spend_nano[budget.id]['media'] += attributed_media_nano
        per_budget_spend_nano[budget.id]['data'] += attributed_data_nano
        per_budget_spend_nano[budget.id]['license_fee'] += license_fee_nano

        total_media_nano -= attributed_media_nano
        total_data_nano -= attributed_data_nano
        reports.models.BudgetDailyStatement.objects.create(
            budget_id=budget.id,
            date=date,
            media_spend_nano=attributed_media_nano,
            data_spend_nano=attributed_data_nano,
            license_fee_nano=license_fee_nano
        )

    if total_media_nano + total_data_nano > 0:
        # TODO: over spend
        pass


def _get_dates(date, campaign):
    budgets = dash.models.BudgetLineItem.objects.filter(campaign_id=campaign.id)
    existing_statements = reports.models.BudgetDailyStatement.objects.filter(budget__campaign_id=campaign.id)

    if budgets.count() == 0:
        return []

    by_date = defaultdict(dict)
    for existing_statement in existing_statements:
        by_date[existing_statement.date][existing_statement.budget_id] = existing_statement

    today = dates_helper.local_today()
    from_date = min(date, *(budget.start_date for budget in budgets))
    to_date = min(max(budget.end_date for budget in budgets), today)
    while True:
        found = False
        for budget in budgets:
            if budget.start_date <= from_date <= budget.end_date and budget.id not in by_date[from_date]:
                found = True

        if found or from_date == date or from_date == to_date:
            break

        from_date += datetime.timedelta(days=1)

    return [dt.date() for dt in rrule.rrule(rrule.DAILY, dtstart=from_date, until=to_date)]


def get_effective_spend_pcts(date, campaign):
    attributed_spends = reports.models.BudgetDailyStatement.objects.\
        filter(budget__campaign=campaign, date=date).\
        aggregate(
            media_nano=Sum('media_spend_nano'),
            data_nano=Sum('data_spend_nano'),
            license_fee_nano=Sum('license_fee_nano')
        )
    actual_spends = reports.models.AdGroupStats.objects.\
        filter(ad_group__campaign_id=campaign.id, datetime=date).\
        aggregate(
            media_cc=Sum('cost_cc'),
            data_cc=Sum('data_cost_cc')
        )
    actual_spend_nano = (actual_spends['media_cc'] or 0) * CC_TO_NANO + (actual_spends['data_cc'] or 0) * CC_TO_NANO
    attributed_spend_nano = (attributed_spends['media_nano'] or 0) + (attributed_spends['data_nano'] or 0)
    license_fee_nano = attributed_spends['license_fee_nano'] or 0

    pct_actual_spend = 0
    if actual_spend_nano > 0:
        pct_actual_spend = min(1, attributed_spend_nano / Decimal(actual_spend_nano))

    pct_license_fee = 0
    if attributed_spend_nano > 0:
        pct_license_fee = min(1, license_fee_nano / Decimal(attributed_spend_nano))

    return pct_actual_spend, pct_license_fee


@transaction.atomic
def reprocess_daily_statements(date, campaign):
    dates = _get_dates(date, campaign)
    for date in dates:
        _generate_statements(date, campaign)
    return dates
