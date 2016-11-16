import backtosql
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
from utils import converters

from redshiftapi import db

from etl import helpers

logger = logging.getLogger(__name__)


def _generate_statements(date, campaign, campaign_spend):
    logger.info("Generate daily statements for %s, %s: %s", campaign.id, date, campaign_spend)

    budgets = dash.models.BudgetLineItem.objects.filter(campaign_id=campaign.id,
                                                        start_date__lte=date,
                                                        end_date__gte=date)

    existing_statements = reports.models.BudgetDailyStatement.objects.filter(
        date__lte=date,
        budget__campaign_id=campaign.id)
    existing_statements.filter(date=date).delete()

    per_budget_spend_nano = defaultdict(lambda: defaultdict(int))
    for existing_statement in existing_statements:
        per_budget_spend_nano[existing_statement.budget_id]['media'] += existing_statement.media_spend_nano
        per_budget_spend_nano[existing_statement.budget_id]['data'] += existing_statement.data_spend_nano
        per_budget_spend_nano[existing_statement.budget_id]['license_fee'] += existing_statement.license_fee_nano

    if campaign_spend is not None:
        total_media_nano = campaign_spend['media_nano']
        total_data_nano = campaign_spend['data_nano']
    else:
        total_media_nano = 0
        total_data_nano = 0

    for budget in budgets.order_by('created_dt'):
        budget_amount_nano = budget.amount * converters.DOLAR_TO_NANO
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

        margin_nano = (attributed_media_nano + attributed_data_nano + license_fee_nano) * budget.margin
        reports.models.BudgetDailyStatement.objects.create(
            budget_id=budget.id,
            date=date,
            media_spend_nano=attributed_media_nano,
            data_spend_nano=attributed_data_nano,
            license_fee_nano=license_fee_nano,
            margin_nano=margin_nano,
        )

    if total_media_nano + total_data_nano > 0:
        # overspend occured, can be handled here
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

    while from_date <= to_date and from_date < date:
        found = False
        for budget in budgets:
            if budget.start_date <= from_date <= budget.end_date and budget.id not in by_date[from_date]:
                found = True

        if found:
            break

        from_date += datetime.timedelta(days=1)

    return [dt.date() for dt in rrule.rrule(rrule.DAILY, dtstart=from_date, until=to_date)]


def _get_effective_spend_pcts(date, campaign, campaign_spend):
    if campaign_spend is None:
        return 0, 0, 0

    attributed_spends = reports.models.BudgetDailyStatement.objects.\
        filter(budget__campaign=campaign, date=date).\
        aggregate(
            media_nano=Sum('media_spend_nano'),
            data_nano=Sum('data_spend_nano'),
            license_fee_nano=Sum('license_fee_nano'),
            margin_nano=Sum('margin_nano'),
        )

    actual_spend_nano = campaign_spend['media_nano'] + campaign_spend['data_nano']
    attributed_spend_nano = (attributed_spends['media_nano'] or 0) + (attributed_spends['data_nano'] or 0)
    license_fee_nano = attributed_spends['license_fee_nano'] or 0
    margin_nano = attributed_spends['margin_nano'] or 0

    pct_actual_spend = 0
    if actual_spend_nano > 0:
        pct_actual_spend = min(1, attributed_spend_nano / Decimal(actual_spend_nano))

    pct_license_fee = 0
    if attributed_spend_nano > 0:
        pct_license_fee = min(1, license_fee_nano / Decimal(attributed_spend_nano))

    pct_margin = 0
    if attributed_spend_nano + license_fee_nano > 0:
        pct_margin = min(1, margin_nano / Decimal(attributed_spend_nano + license_fee_nano))

    return pct_actual_spend, pct_license_fee, pct_margin


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

    query = """
        select ad_group_id, sum(spend), sum(data_spend)
        from stats
        where {date_query}
        group by ad_group_id
    """.format(date_query=helpers.get_local_date_query(date))

    logger.info("Running redshift query: %s", query)

    with connections[settings.STATS_DB_NAME].cursor() as c:
        c.execute(query)

        for ad_group_id, media_spend, data_spend in c:
            campaign_id = ad_group_campaign.get(ad_group_id)
            if campaign_id is None:
                if media_spend > 0 or data_spend > 0:
                    logger.info("Got spend for invalid adgroup: %s", ad_group_id)
                continue

            if media_spend is None:
                media_spend = 0
            if data_spend is None:
                data_spend = 0

            campaign_spend[campaign_id]['media_nano'] += media_spend * converters.MICRO_TO_NANO
            campaign_spend[campaign_id]['data_nano'] += data_spend * converters.MICRO_TO_NANO

    return campaign_spend


def get_campaigns_with_spend(date_since):

    today = dates_helper.local_today()
    past_date = today - datetime.timedelta(days=dash.models.NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL)
    past_date = max(past_date, date_since)

    params = helpers.get_local_multiday_date_context(past_date, today)
    del params['date_ranges']  # unnecessary in this case

    ad_group_ids = _query_ad_groups_with_spend(params)

    campaign_ids = dash.models.AdGroup.objects.filter(pk__in=ad_group_ids)\
                                              .values_list('campaign_id', flat=True)\
                                              .distinct('campaign_id')\
                                              .order_by('campaign_id')
    return dash.models.Campaign.objects.filter(pk__in=campaign_ids)


def _query_ad_groups_with_spend(params):
    sql = backtosql.generate_sql('etl_ad_groups_with_spend.sql', None)

    with db.get_stats_cursor() as cursor:
        cursor.execute(sql, params)
        ad_group_ids = [x for x, in cursor]  # row is a tuple

    return ad_group_ids


@transaction.atomic
def _reprocess_campaign_statements(campaign, dates, total_spend):
    for date in dates:
        _generate_statements(date, campaign, total_spend[date].get(campaign.id))
    return dates


def reprocess_daily_statements(date_since):
    logger.info("Reprocessing dailiy statements for %s", date_since)

    total_spend = {}
    all_dates = set()

    campaigns = dash.models.Campaign.objects.prefetch_related('adgroup_set').all().exclude_archived()

    # get campaigns that have spend in the last 3 days and might be archived
    campaigns_w_spend = get_campaigns_with_spend(date_since)

    logger.info(
        "Additional campaigns with spend %s",
        set(campaigns_w_spend.values_list('pk', flat=True)) - set(campaigns.values_list('pk', flat=True)))

    campaigns |= campaigns_w_spend

    for campaign in campaigns:
        # extracts dates where we have budgets but are not linked to daily statements

        # get dates for a single campaign
        dates = _get_dates(date_since, campaign)
        for date in dates:
            all_dates.add(date)
            if date not in total_spend:
                # do it for all campaigns at once for a single date
                total_spend[date] = _get_campaign_spend(date, campaigns)

        _reprocess_campaign_statements(campaign, dates, total_spend)

    effective_spend = defaultdict(lambda: {})
    for campaign in dash.models.Campaign.objects.all():
        for date in all_dates:
            spend = total_spend[date].get(campaign.id)
            effective_spend[date][campaign] = _get_effective_spend_pcts(date, campaign, spend)

    return dict(effective_spend)
