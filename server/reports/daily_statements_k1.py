from collections import defaultdict
from decimal import Decimal
import datetime
import logging

from dateutil import rrule
from django.db import transaction
from django.db.models import Sum
from django.db import connections
from django.conf import settings

import dash.models
import reports.models
from utils import dates_helper

logger = logging.getLogger(__name__)

CC_TO_NANO = int(1E5)
DOLAR_TO_NANO = int(1E9)
MICRO_TO_NANO = int(1E3)


def _generate_statements(date, campaign, campaign_spend):
    logger.info("Generate daily statements for %s, %s: %s", campaign.id, date, campaign_spend)

    budgets = dash.models.BudgetLineItem.objects.filter(campaign_id=campaign.id,
                                                        start_date__lte=date,
                                                        end_date__gte=date)

    existing_statements = reports.models.BudgetDailyStatementK1.objects.filter(
        date__lte=date,
        budget__campaign_id=campaign.id)
    existing_statements.filter(date=date).delete()

    per_budget_spend_nano = defaultdict(lambda: defaultdict(int))
    for existing_statement in existing_statements:
        per_budget_spend_nano[existing_statement.budget_id]['media'] += existing_statement.media_spend_nano
        per_budget_spend_nano[existing_statement.budget_id]['data'] += existing_statement.data_spend_nano
        per_budget_spend_nano[existing_statement.budget_id]['license_fee'] += existing_statement.license_fee_nano

    total_media_nano = campaign_spend['media_nano']
    total_data_nano = campaign_spend['data_nano']

    for budget in budgets.order_by('created_dt'):
        budget_amount_nano = budget.amount * DOLAR_TO_NANO
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
        reports.models.BudgetDailyStatementK1.objects.create(
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
    existing_statements = reports.models.BudgetDailyStatementK1.objects.filter(budget__campaign_id=campaign.id)

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

        if found or from_date == date or from_date > to_date:
            break

        from_date += datetime.timedelta(days=1)

    return [dt.date() for dt in rrule.rrule(rrule.DAILY, dtstart=from_date, until=to_date)]


def get_effective_spend_pcts(date, campaign, campaign_spend):
    attributed_spends = reports.models.BudgetDailyStatementK1.objects.\
        filter(budget__campaign=campaign, date=date).\
        aggregate(
            media_nano=Sum('media_spend_nano'),
            data_nano=Sum('data_spend_nano'),
            license_fee_nano=Sum('license_fee_nano')
        )

    actual_spend_nano = campaign_spend['media_nano'] + campaign_spend['data_nano']
    attributed_spend_nano = (attributed_spends['media_nano'] or 0) + (attributed_spends['data_nano'] or 0)
    license_fee_nano = attributed_spends['license_fee_nano'] or 0

    pct_actual_spend = 0
    if actual_spend_nano > 0:
        pct_actual_spend = min(1, attributed_spend_nano / Decimal(actual_spend_nano))

    pct_license_fee = 0
    if attributed_spend_nano > 0:
        pct_license_fee = min(1, license_fee_nano / Decimal(attributed_spend_nano))

    return pct_actual_spend, pct_license_fee


def _get_campaign_spend(date, all_campaigns):
    logger.info("Fetching campaign spend for %s", date)

    campaign_spend = {}
    ad_group_campaign = {}
    for campaign in all_campaigns:
        campaign_spend[campaign.id] = {
            'media_nano': 0,
            'data_nano': 0,
        }
        for ad_group in campaign.adgroup_set.all():
            ad_group_campaign[ad_group.id] = campaign.id

    cursor = connections[settings.STATS_DB_NAME].cursor()

    query = """
        select ad_group_id, sum(spend), sum(data_spend)
        from stats
        where {date_query}
        group by ad_group_id
    """.format(date_query=_get_redshift_date_query(date))

    logger.info("Running redshift query: %s", query)
    cursor.execute(query)

    for ad_group_id, media_spend, data_spend in cursor.fetchall():
        campaign_id = ad_group_campaign.get(ad_group_id)
        if campaign_id is None:
            logger.warn("Got spend for archived adgroup: %s", ad_group_id)

        if media_spend is None:
            media_spend = 0
        if data_spend is None:
            data_spend = 0

        campaign_spend[campaign_id]['media_nano'] += media_spend * MICRO_TO_NANO
        campaign_spend[campaign_id]['data_nano'] += data_spend * MICRO_TO_NANO

    return campaign_spend


def _get_redshift_date_query(date):
    hour_from = dates_helper.local_to_utc_time(datetime.datetime(date.year, date.month, date.day))
    date_next = date + datetime.timedelta(days=1)
    hour_to = dates_helper.local_to_utc_time(datetime.datetime(date_next.year, date_next.month, date_next.day))

    query = """
    (date = '{date}' and hour = -1) or (
        hour >= 0 and (
            (date = '{tzdate_from}' and hour >= {tzhour_from}) or
            (date = '{tzdate_to}' and hour < {tzhour_to})
        )
    )
    """.format(
        date=date.isoformat(),
        tzdate_from=hour_from.date().isoformat(),
        tzhour_from=hour_from.hour,
        tzdate_to=hour_to.date().isoformat(),
        tzhour_to=hour_to.hour,
    )

    return query


@transaction.atomic
def _reprocess_campaign_statements(campaign, dates, total_spend):
    for date in dates:
        _generate_statements(date, campaign, total_spend[date][campaign.id])
    return dates


def reprocess_daily_statements(date_since):
    logger.info("Reprocessing dailiy statements for %s", date_since)

    total_spend = {}

    campaigns = dash.models.Campaign.objects.prefetch_related('adgroup_set').all().exclude_archived()
    for campaign in campaigns:
        dates = _get_dates(date_since, campaign)
        for date in dates:
            if date not in total_spend:
                total_spend[date] = _get_campaign_spend(date, campaigns)

        _reprocess_campaign_statements(campaign, dates, total_spend)
