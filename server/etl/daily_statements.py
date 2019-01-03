import datetime
import logging
from collections import defaultdict
from decimal import Decimal

from dateutil import rrule
from django.conf import settings
from django.db import connections
from django.db import transaction
from django.db.models import Max
from django.db.models import Sum

import backtosql
import core.features.bcm.calculations
import dash.models
from etl import helpers
from redshiftapi import db
from utils import converters
from utils import dates_helper

logger = logging.getLogger(__name__)

FIXED_MARGIN_START_DATE = datetime.date(2017, 6, 21)


def _generate_statements(date, campaign, campaign_spend):
    logger.debug("Generate daily statements for %s, %s: %s", campaign.id, date, campaign_spend)

    budgets = dash.models.BudgetLineItem.objects.filter(
        campaign_id=campaign.id, start_date__lte=date, end_date__gte=date
    ).select_related("campaign__account", "credit")

    existing_statements = dash.models.BudgetDailyStatement.objects.filter(
        date__lte=date, budget__campaign_id=campaign.id
    )
    existing_statements.filter(date=date).delete()

    local_per_budget_spend_nano = defaultdict(lambda: defaultdict(int))
    for existing_statement in existing_statements:
        local_per_budget_spend_nano[existing_statement.budget_id]["media"] += existing_statement.local_media_spend_nano
        local_per_budget_spend_nano[existing_statement.budget_id]["data"] += existing_statement.local_data_spend_nano
        local_per_budget_spend_nano[existing_statement.budget_id][
            "license_fee"
        ] += existing_statement.local_license_fee_nano
        local_per_budget_spend_nano[existing_statement.budget_id]["margin"] += existing_statement.local_margin_nano

    if campaign_spend is not None:
        total_media_nano = campaign_spend["media_nano"]
        total_data_nano = campaign_spend["data_nano"]
    else:
        total_media_nano = 0
        total_data_nano = 0

    for budget in budgets.order_by("created_dt"):
        local_budget_amount_nano = budget.allocated_amount() * converters.CURRENCY_TO_NANO
        attributed_media_nano = 0
        attributed_data_nano = 0
        license_fee_nano = 0
        margin_nano = 0

        total_spend_nano = total_media_nano + total_data_nano
        local_budget_spend_total_nano = (
            local_per_budget_spend_nano[budget.id]["media"]
            + local_per_budget_spend_nano[budget.id]["data"]
            + local_per_budget_spend_nano[budget.id]["license_fee"]
        )
        if budget.start_date >= FIXED_MARGIN_START_DATE:
            local_budget_spend_total_nano += local_per_budget_spend_nano[budget.id]["margin"]

        if total_spend_nano > 0 and local_budget_spend_total_nano < local_budget_amount_nano:
            local_available_budget_nano = local_budget_amount_nano - local_budget_spend_total_nano
            usd_available_budget_nano = local_available_budget_nano / core.features.multicurrency.get_exchange_rate(
                date, budget.credit.currency
            )
            if budget.start_date >= FIXED_MARGIN_START_DATE:
                usd_available_budget_nano = usd_available_budget_nano * (1 - budget.margin)
            usd_available_budget_nano = usd_available_budget_nano * (1 - budget.credit.license_fee)

            if total_media_nano + total_data_nano > usd_available_budget_nano:
                if total_media_nano >= usd_available_budget_nano:
                    attributed_media_nano = usd_available_budget_nano
                    attributed_data_nano = 0
                else:
                    attributed_media_nano = total_media_nano
                    attributed_data_nano = usd_available_budget_nano - total_media_nano
            else:
                attributed_media_nano = total_media_nano
                attributed_data_nano = total_data_nano

            license_fee_nano = core.features.bcm.calculations.calculate_fee(
                attributed_media_nano + attributed_data_nano, budget.credit.license_fee
            )
            if budget.start_date >= FIXED_MARGIN_START_DATE:
                margin_nano = core.features.bcm.calculations.calculate_margin(
                    attributed_media_nano + attributed_data_nano + license_fee_nano, budget.margin
                )

        local_per_budget_spend_nano[budget.id]["media"] += attributed_media_nano
        local_per_budget_spend_nano[budget.id]["data"] += attributed_data_nano
        local_per_budget_spend_nano[budget.id]["license_fee"] += license_fee_nano
        local_per_budget_spend_nano[budget.id]["margin"] += margin_nano

        total_media_nano -= attributed_media_nano
        total_data_nano -= attributed_data_nano

        if budget.start_date < FIXED_MARGIN_START_DATE:
            margin_nano = (attributed_media_nano + attributed_data_nano + license_fee_nano) * budget.margin

        dash.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=date,
            media_spend_nano=attributed_media_nano,
            data_spend_nano=attributed_data_nano,
            license_fee_nano=license_fee_nano,
            margin_nano=margin_nano,
        )

    if total_media_nano > 0 or total_data_nano > 0:
        try:
            _handle_overspend(date, campaign, total_media_nano, total_data_nano)
        except Exception:
            logger.exception("Failed to handle overspend for campaign %s on date %s", campaign.id, date)


def _handle_overspend(date, campaign, media_nano, data_nano):
    if campaign.real_time_campaign_stop:
        return

    try:
        budget = dash.models.BudgetLineItem.objects.filter(
            campaign_id=campaign.id, start_date__lte=date, end_date__gte=date
        ).latest("created_dt")
    except dash.models.BudgetLineItem.DoesNotExist:
        credit = dash.models.CreditLineItem.objects.filter(
            account_id=campaign.account_id, start_date__lte=date, end_date__gte=date
        ).latest("created_dt")

        budget = dash.models.BudgetLineItem.objects.create_unsafe(
            credit=credit,
            campaign_id=campaign.id,
            start_date=date,
            end_date=date,
            amount=0,
            comment="Budget created automatically",
        )

    try:
        daily_statement = budget.statements.get(date=date)
    except dash.models.BudgetDailyStatement.DoesNotExist:
        daily_statement = dash.models.BudgetDailyStatement.objects.create(
            budget=budget, date=date, media_spend_nano=0, data_spend_nano=0, license_fee_nano=0, margin_nano=0
        )

    license_fee_nano = core.features.bcm.calculations.calculate_fee(media_nano + data_nano, budget.credit.license_fee)
    if budget.start_date >= FIXED_MARGIN_START_DATE:
        margin_nano = core.features.bcm.calculations.calculate_margin(
            media_nano + data_nano + license_fee_nano, budget.margin
        )
    else:
        margin_nano = (media_nano + data_nano + license_fee_nano) * budget.margin

    daily_statement.update_amounts(
        media_spend_nano=daily_statement.media_spend_nano + media_nano,
        data_spend_nano=daily_statement.data_spend_nano + data_nano,
        license_fee_nano=daily_statement.license_fee_nano + license_fee_nano,
        margin_nano=daily_statement.margin_nano + margin_nano,
    )


def _get_dates(from_date, campaign):
    if campaign.max_budget_end_date is None:
        return []

    today = dates_helper.local_today()
    to_date = min(campaign.max_budget_end_date, today)

    return [dt.date() for dt in rrule.rrule(rrule.DAILY, dtstart=from_date, until=to_date)]


def get_effective_spend(total_spend, date_since, account_id=None):

    campaigns = dash.models.Campaign.objects.all()
    if account_id:
        campaigns = campaigns.filter(account_id=account_id)

    total_spend = _fetch_total_spend(total_spend, campaigns, date_since, account_id)
    all_dates = list(total_spend.keys())

    all_attributed_spends = (
        dash.models.BudgetDailyStatement.objects.filter(budget__campaign__in=campaigns, date__in=all_dates)
        .values("budget__campaign__id", "date")
        .annotate(
            media_nano=Sum("media_spend_nano"),
            data_nano=Sum("data_spend_nano"),
            license_fee_nano=Sum("license_fee_nano"),
            margin_nano=Sum("margin_nano"),
        )
    )

    attributed_spends = defaultdict(dict)
    for spend in all_attributed_spends:
        attributed_spends[spend["budget__campaign__id"]][spend["date"]] = spend

    effective_spend = defaultdict(dict)
    for campaign in campaigns:
        for date in all_dates:
            spend = total_spend[date].get(campaign.id)
            effective_spend[date][campaign] = _get_effective_spend_pcts(
                date, campaign, spend, attributed_spends[campaign.id].get(date, {})
            )

    return dict(effective_spend)


def _get_effective_spend_pcts(date, campaign, campaign_spend, attributed_spends):
    if campaign_spend is None:
        return 0, 0, 0

    actual_spend_nano = campaign_spend["media_nano"] + campaign_spend["data_nano"]
    attributed_spend_nano = (attributed_spends.get("media_nano") or 0) + (attributed_spends.get("data_nano") or 0)
    license_fee_nano = attributed_spends.get("license_fee_nano") or 0
    margin_nano = attributed_spends.get("margin_nano") or 0

    pct_actual_spend = 0
    if actual_spend_nano > 0:
        pct_actual_spend = min(1, attributed_spend_nano / Decimal(actual_spend_nano))

    pct_license_fee = 0
    if attributed_spend_nano > 0:
        pct_license_fee = min(1, license_fee_nano / Decimal(attributed_spend_nano))

    pct_margin = 0
    if attributed_spend_nano + license_fee_nano > 0:
        pct_margin = margin_nano / Decimal(attributed_spend_nano + license_fee_nano)

    return pct_actual_spend, pct_license_fee, pct_margin


def _get_campaign_spend(date, all_campaigns, account_id):
    logger.info("Fetching campaign spend for %s", date)

    campaign_spend = {}
    ad_group_campaign = {}
    for campaign in all_campaigns:
        campaign_spend[campaign.id] = {"media_nano": 0, "data_nano": 0}
        for ad_group in campaign.adgroup_set.all():
            ad_group_campaign[ad_group.id] = campaign.id

    if account_id:
        ad_group_ids = helpers.get_ad_group_ids_or_none(account_id)
        query = """
        select ad_group_id, sum(spend), sum(data_spend)
        from (SELECT * FROM stats_diff UNION ALL SELECT * FROM stats) AS stats
        where ({date_query}) and ad_group_id IN ({ad_group_ids})
        group by ad_group_id
        """.format(
            date_query=helpers.get_local_date_query(date), ad_group_ids=",".join(str(x) for x in ad_group_ids)
        )
    else:
        query = """
        select ad_group_id, sum(spend), sum(data_spend)
        from (SELECT * FROM stats_diff UNION ALL SELECT * FROM stats) AS stats
        where {date_query}
        group by ad_group_id
        """.format(
            date_query=helpers.get_local_date_query(date)
        )

    logger.debug("Running redshift query: %s", query)

    with connections[settings.STATS_DB_NAME].cursor() as c:
        c.execute(query)

        for ad_group_id, media_spend, data_spend in c:
            if media_spend is None:
                media_spend = 0
            if data_spend is None:
                data_spend = 0

            campaign_id = ad_group_campaign.get(ad_group_id)
            if campaign_id is None:
                if media_spend > 0 or data_spend > 0:
                    logger.info("Got spend for adgroup in campaign that is not being reprocessed: %s", ad_group_id)
                    campaign_id = dash.models.AdGroup.objects.get(pk=ad_group_id).campaign_id
                    campaign_spend[campaign_id] = {"media_nano": 0, "data_nano": 0}
                continue

            campaign_spend[campaign_id]["media_nano"] += media_spend * converters.MICRO_TO_NANO
            campaign_spend[campaign_id]["data_nano"] += data_spend * converters.MICRO_TO_NANO

    return campaign_spend


def get_campaigns_with_spend(date_since):

    today = dates_helper.local_today()

    params = helpers.get_local_multiday_date_context(date_since, today)
    del params["date_ranges"]  # unnecessary in this case

    ad_group_ids = _query_ad_groups_with_spend(params)

    campaign_ids = (
        dash.models.AdGroup.objects.filter(pk__in=ad_group_ids)
        .values_list("campaign_id", flat=True)
        .distinct("campaign_id")
        .order_by("campaign_id")
    )
    return dash.models.Campaign.objects.filter(pk__in=campaign_ids)


def get_campaigns_with_budgets_in_timeframe(date_since):
    today = dates_helper.local_today()
    return dash.models.Campaign.objects.filter(budgets__start_date__lte=today, budgets__end_date__gte=date_since)


def _query_ad_groups_with_spend(params):
    sql = backtosql.generate_sql("etl_ad_groups_with_spend.sql", None)

    with db.get_stats_cursor() as cursor:
        cursor.execute(sql, params)
        ad_group_ids = [x for x, in cursor]  # row is a tuple

    return ad_group_ids


@transaction.atomic
def _reprocess_campaign_statements(campaign, dates, total_spend):
    for date in dates:
        _generate_statements(date, campaign, total_spend[date].get(campaign.id))
    return dates


def reprocess_daily_statements(date_since, account_id=None):
    logger.info("Reprocessing dailiy statements for %s %s", date_since, account_id)

    total_spend = {}
    all_dates = set()

    campaigns = dash.models.Campaign.objects.prefetch_related("adgroup_set").all().exclude_archived(bool(account_id))

    # Get campaigns that have spend in the time frame we're reprocessing. This is necessary because some campaigns might
    # already be archived.
    campaigns_w_spend = get_campaigns_with_spend(date_since)

    logger.info(
        "Additional campaigns with spend %s",
        set(campaigns_w_spend.values_list("pk", flat=True)) - set(campaigns.values_list("pk", flat=True)),
    )

    # Get campaigns that have budget start & end dates in the time frame we're reprocessing.
    # This is done so that all budgets have daily statements for every day between start&end date, even if they're already
    # depleted.
    campaigns_w_budgets_in_timeframe = get_campaigns_with_budgets_in_timeframe(date_since)

    logger.info(
        "Additional campaigns with budgets in this timeframe %s",
        set(campaigns_w_budgets_in_timeframe.values_list("pk", flat=True))
        - set(campaigns.values_list("pk", flat=True)),
    )

    campaigns |= campaigns_w_spend
    campaigns |= campaigns_w_budgets_in_timeframe

    if account_id:
        campaigns = campaigns.filter(account_id=account_id)

    campaigns = campaigns.annotate(max_budget_end_date=Max("budgets__end_date"))

    for campaign in campaigns:
        # extracts dates where we have budgets but are not linked to daily statements

        # get dates for a single campaign
        dates = _get_dates(date_since, campaign)
        for date in dates:
            all_dates.add(date)
            if date not in total_spend:
                # do it for all campaigns at once for a single date
                logger.info("Fetching spend for %s because of campaign %s" % (date, campaign.id))
                total_spend[date] = _get_campaign_spend(date, campaigns, account_id)

        # generate daily statements for the date for the campaign
        _reprocess_campaign_statements(campaign, dates, total_spend)

    return total_spend


def _fetch_total_spend(total_spend, campaigns, date_since, account_id):
    campaigns = campaigns.prefetch_related("adgroup_set")

    all_dates = list(total_spend.keys())
    start_date = min(date_since, min(all_dates)) if len(all_dates) > 0 else date_since
    end_date = dates_helper.local_today()
    # It can happen that not all of the dates in the range need to have their daily statements
    # reprocessed. When this happens total_spend and all_dates will have have some dates missing.
    # We need to assure that we provide campaign factors for all the dates within the range we
    # are processing. The following statements add campaign spend for the missing dates:
    for dt in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date):
        date = dt.date()
        if date not in total_spend:
            logger.info("Fetching spend for the date %s that wasn't reprocessed", date)
            total_spend[date] = _get_campaign_spend(date, campaigns, account_id)

    return total_spend
