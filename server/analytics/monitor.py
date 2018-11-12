import datetime
import logging
from decimal import Decimal

from django.db.models import F
from django.db.models import Sum

import analytics.helpers
import analytics.projections
import automation.models
import backtosql
import dash.constants
import dash.models
import etl.refresh
import redshiftapi.db
from automation import autopilot
from utils import converters

logger = logging.getLogger("stats.monitor")

MAX_ERR = 10 ** 7  # 0.01$

API_ACCOUNTS = (293, 305)


def _get_rs_spend(table_name, date, account_id=None):
    additional = ""
    if account_id:
        additional = " AND account_id = {}".format(account_id)
    with redshiftapi.db.get_stats_cursor() as c:
        spend_integrity_query = backtosql.generate_sql(
            "sql/monitor_spend_integrity.sql", dict(tbl=table_name, d=str(date), additional=additional)
        )
        c.execute(spend_integrity_query)
        return redshiftapi.db.dictfetchall(c)[0]
    return {}


def audit_spend_integrity(date, account_id=None, max_err=MAX_ERR):
    if date is None:
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)
    spend_queryset = dash.models.BudgetDailyStatement.objects.filter(date=date)
    if account_id:
        spend_queryset = spend_queryset.filter(budget__campaign__account_id=account_id)
    daily_spend = spend_queryset.values("date").annotate(
        media=Sum(F("media_spend_nano")),
        data=Sum(F("data_spend_nano")),
        margin=Sum(F("margin_nano")),
        fee=Sum(F("license_fee_nano")),
    )[0]
    integrity_issues = []
    for table_name in etl.refresh.get_all_views_table_names():

        if "pubs" in table_name or "conversions" in table_name or "touch" in table_name:
            # skip for the first version
            continue
        if table_name.endswith("_conv"):
            # skip for the first version
            continue
        rs_spend = _get_rs_spend(table_name, date, account_id=account_id)
        for key in rs_spend:
            err = daily_spend[key] - rs_spend[key]
            if abs(err) > max_err:
                integrity_issues.append((date, table_name, key, err))
    return integrity_issues


def audit_spend_patterns(date=None, threshold=0.8, first_in_month_threshold=0.6, day_range=3):
    if date is None:
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)
    total_spend = Sum(F("media_spend_nano") + F("data_spend_nano") + F("license_fee_nano"))
    result = (
        dash.models.BudgetDailyStatement.objects.filter(date__lte=date, date__gte=date - datetime.timedelta(day_range))
        .values("date")
        .annotate(total=total_spend)
        .order_by("date")
    )
    totals = [row["total"] for row in result]
    # check the difference in the total between date -1 and date -2 then date -2 and date -3 ....
    changes = [(date + datetime.timedelta(-x), float(totals[-x - 1]) / totals[-x - 2]) for x in range(0, day_range - 1)]
    alarming_dates = [
        (d, change)
        for d, change in changes
        if d.day == 1 and change < first_in_month_threshold or d.day != 1 and change < threshold
    ]
    return alarming_dates


def audit_pacing(date, max_pacing=Decimal("200.0"), min_pacing=Decimal("50.0"), **constraints):
    # fixme tfischer 05/11/18: Paused until account types are properly marked. INPW is considered activated.
    if date is None:
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)

    monthly_proj = analytics.projections.CurrentMonthBudgetProjections("campaign", date=date, **constraints)
    alarms = []
    for campaign_id in list(monthly_proj.keys()):
        pacing = monthly_proj.row(campaign_id)["pacing"]
        if pacing is None:
            continue
        if pacing > max_pacing:
            alarms.append((campaign_id, pacing, "high", monthly_proj.row(campaign_id)))
        if pacing < min_pacing:
            alarms.append((campaign_id, pacing, "low", monthly_proj.row(campaign_id)))
    return alarms


def audit_autopilot_ad_groups():
    date = datetime.date.today()
    ap_logs = automation.models.AutopilotLog.objects.filter(
        created_dt__range=(
            datetime.datetime.combine(date, datetime.time.min),
            datetime.datetime.combine(date, datetime.time.max),
        ),
        is_autopilot_job_run=True,
        ad_group__created_dt__lt=date,
    )
    ad_groups_in_logs = set(log.ad_group for log in ap_logs)
    ad_groups_ap_running = set(
        ad
        for ad in autopilot.helpers.get_active_ad_groups_on_autopilot()[0]
        if ad.created_dt < datetime.datetime.combine(date, datetime.time.min)
    )
    return ad_groups_ap_running - ad_groups_in_logs


def audit_autopilot_cpc_changes(date=None, min_changes=25):
    """
    When Autopilot modifies the daily cap, all modifications should not be all positive or all negative, it should
    be balanced.
    """
    if not date:
        date = datetime.date.today()
    ap_logs = automation.models.AutopilotLog.objects.filter(
        created_dt__range=(
            datetime.datetime.combine(date, datetime.time.min),
            datetime.datetime.combine(date, datetime.time.max),
        ),
        is_autopilot_job_run=True,
        ad_group_source__source__deprecated=False,
        ad_group_source__source__maintenance=False,
        ad_group_source__source__released=True,
    )
    source_changes = {}
    for log in ap_logs:
        source_changes.setdefault(log.ad_group_source.source, []).append(log.new_cpc_cc - log.previous_cpc_cc)
    alarms = {}
    for source, changes in source_changes.items():
        if len(changes) < min_changes:
            continue
        positive_changes = [x for x in changes if x >= 0]
        negative_changes = [x for x in changes if x <= 0]
        if len(positive_changes) == len(changes):
            alarms[source] = sum(positive_changes)
        if len(negative_changes) == len(changes):
            alarms[source] = sum(negative_changes)
    return alarms


def audit_autopilot_daily_caps_changes(date=None, error=Decimal("0.001")):
    """
    Autopilot is modifying the daily cap of each source, by taking some money from the sources performing bad
    to assign it to sources performing the best. But at the end the total of all sources's daily cap must be the same.
    """
    if not date:
        date = datetime.date.today()
    ap_logs = automation.models.AutopilotLog.objects.filter(
        created_dt__range=(
            datetime.datetime.combine(date, datetime.time.min),
            datetime.datetime.combine(date, datetime.time.max),
        ),
        is_autopilot_job_run=True,
        ad_group_source__source__deprecated=False,
        ad_group_source__source__maintenance=False,
        autopilot_type=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
    ).exclude(ad_group__in=dash.models.AdGroup.objects.all())
    total_changes = {}
    for log in ap_logs:
        if not log.new_daily_budget or not log.previous_daily_budget:
            continue
        total_changes.setdefault(log.ad_group, []).append(log.new_daily_budget - log.previous_daily_budget)
    alarms = {}
    for ad_group, changes in total_changes.items():
        budget_changes = sum(changes)
        if not budget_changes or abs(budget_changes) > error:
            alarms[ad_group] = budget_changes
    return alarms


def audit_overspend(date, min_overspend=Decimal("0.1")):
    overspend_query = backtosql.generate_sql(
        "sql/monitor_overspend.sql",
        dict(date=str(date), threshold=str(int(min_overspend * converters.CURRENCY_TO_NANO))),
    )
    rows = redshiftapi.db.execute_query(overspend_query, [], "audit_overspend")
    accounts_map = {account.id: account for account in dash.models.Account.objects.all()}
    alarms = {}
    for row in rows:
        account = accounts_map[row["account_id"]]
        alarms[account] = converters.nano_to_decimal(row["diff"])
    return alarms


def audit_running_ad_groups(min_spend=Decimal("50.0"), account_types=None):
    """
    Alert how many ad groups had a very low spend
    Audit ad groups spend of non API active ad groups of types:
    - PILOT
    - ACTIVATED
    - MANAGED
    """
    if not account_types:
        account_types = (
            dash.constants.AccountType.PILOT,
            dash.constants.AccountType.ACTIVATED,
            dash.constants.AccountType.MANAGED,
        )
    yesterday = datetime.date.today() - datetime.timedelta(1)
    running_ad_group_ids = set(
        dash.models.AdGroup.objects.all()
        .filter_running(date=yesterday)
        .filter_by_account_types(account_types)
        .values_list("pk", flat=True)
    )
    api_ad_groups = set(
        dash.models.AdGroup.objects.filter(campaign__account_id__in=API_ACCOUNTS).values_list("pk", flat=True)
    )

    with redshiftapi.db.get_stats_cursor() as c:
        ad_group_spend_query = backtosql.generate_sql(
            "sql/monitor_ad_group_spend.sql",
            dict(d=str(yesterday), threshold=str(int(min_spend * converters.CURRENCY_TO_NANO))),
        )
        c.execute(ad_group_spend_query)
        spending_ad_group_ids = set(int(row[0]) for row in c.fetchall())
    return dash.models.AdGroup.objects.filter(pk__in=((running_ad_group_ids - spending_ad_group_ids) - api_ad_groups))


def audit_account_credits(date=None, days=14):

    if not date:
        date = datetime.date.today()
    ending_credit_accounts = set(
        credit.account or credit.agency.account_set.all().first()
        for credit in dash.models.CreditLineItem.objects.filter(
            end_date__gte=date, end_date__lt=date + datetime.timedelta(days)
        )
    )
    future_credit_accounts = set(
        credit.account or credit.agency.account_set.all().first()
        for credit in dash.models.CreditLineItem.objects.filter(end_date__gte=date + datetime.timedelta(days))
    )
    # only accounts with no future credits
    return ending_credit_accounts - future_credit_accounts


def audit_click_discrepancy(date=None, days=30, threshold=20):
    if date is None:
        date = datetime.date.today() - datetime.timedelta(1)
    from_date = date - datetime.timedelta(days + 1)
    till_date = date - datetime.timedelta(1)

    campaigns = {
        c.pk: c
        for c in dash.models.Campaign.objects.filter(
            pk__in=dash.models.CampaignGoal.objects.filter(
                type__in=(
                    dash.constants.CampaignGoalKPI.TIME_ON_SITE,
                    dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE,
                    dash.constants.CampaignGoalKPI.PAGES_PER_SESSION,
                    dash.constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS,
                    dash.constants.CampaignGoalKPI.CPV,
                    dash.constants.CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
                    dash.constants.CampaignGoalKPI.CP_NEW_VISITOR,
                    dash.constants.CampaignGoalKPI.CP_PAGE_VIEW,
                    dash.constants.CampaignGoalKPI.CPCV,
                )
            ).values_list("campaign_id", flat=True)
        )
    }

    data_base, data_test = {}, {}
    with redshiftapi.db.get_stats_cursor() as c:
        click_discrepancy_query = backtosql.generate_sql(
            "sql/monitor_click_discrepancy.sql",
            dict(campaigns=",".join(map(str, list(campaigns.keys()))), from_date=from_date, till_date=till_date),
        )
        c.execute(click_discrepancy_query)
        data_base = {int(r[0]): r[1] for r in c.fetchall()}
        c.execute(click_discrepancy_query)
        data_test = {int(r[0]): r[1] for r in c.fetchall()}

    alarms = []
    for campaign_id in list(data_test.keys()):
        campaign = campaigns.get(campaign_id)
        test = data_test.get(campaign_id)
        base = data_base.get(campaign_id)
        if not campaign or test is None or base is None:
            continue
        change = int(test) - int(base)
        if change > threshold:
            alarms.append((campaign, base, test))
    return alarms


def audit_custom_hacks(minimal_spend=Decimal("0.0001")):
    alarms = []
    for unconfirmed_hack in dash.models.CustomHack.objects.filter(confirmed_by__isnull=True).filter_active(True):
        if unconfirmed_hack.is_global():
            alarms.append((unconfirmed_hack, None))
            continue
        spend = analytics.helpers.get_spend(
            unconfirmed_hack.created_dt.date(),
            ad_group=unconfirmed_hack.ad_group,
            campaign=unconfirmed_hack.campaign,
            account=unconfirmed_hack.account,
            agency=unconfirmed_hack.agency,
        )
        if not spend or ((spend[0]["media"] or Decimal("0")) + (spend[0]["data"] or Decimal("0"))) < minimal_spend:
            continue
        alarms.append(
            (unconfirmed_hack, "media: ${media}, data: ${data}, fee: ${fee}, margin: ${margin}".format(**spend[0]))
        )
    return alarms


def audit_bid_cpc_vs_ecpc(bid_cpc_threshold=2, yesterday_spend_threshold=20):
    yesterday = datetime.date.today() - datetime.timedelta(1)
    active_ad_groups = (
        dash.models.AdGroup.objects.all().filter_running(yesterday).exclude(campaign__account__id__in=API_ACCOUNTS)
    )
    ads_non_exploratory = (
        dash.models.AdGroupSource.objects.filter(ad_group__in=active_ad_groups)
        .filter_active()
        .values("ad_group_id", "source_id", "settings__cpc_cc", "source__name", "ad_group__name")
    )

    ad_group_sources = {
        (ads["ad_group_id"], ads["source_id"]): {
            "cpc": ads["settings__cpc_cc"],
            "source_name": ads["source__name"],
            "name": ads["ad_group__name"],
        }
        for ads in ads_non_exploratory
    }

    with redshiftapi.db.get_stats_cursor() as c:
        yesterday_spend_query = backtosql.generate_sql(
            "sql/monitor_yesterday_spend.sql",
            dict(
                yesterday=yesterday.strftime("%Y-%m-%d"),
                excluded_account_ids=str(API_ACCOUNTS),
                yesterday_spend_threshold=yesterday_spend_threshold,
            ),
        )
        c.execute(yesterday_spend_query)
        yesterday_spends = [
            dict(ad_group_id=i[0], source_id=i[1], total_clicks=i[2], total_spend=i[3], ecpc=i[4]) for i in c.fetchall()
        ]
        alerts = []
        for spend in yesterday_spends:
            ads = ad_group_sources.get((spend["ad_group_id"], spend["source_id"]))
            if not ads:
                continue
            if spend["ecpc"] >= (ads["cpc"] * bid_cpc_threshold):
                higher_yesterday_cpc = dash.models.AdGroupSource.objects.filter(
                    ad_group__id=spend["ad_group_id"],
                    source__id=spend["source_id"],
                    settings__created_dt__range=(
                        datetime.datetime.combine(yesterday, datetime.time.min),
                        datetime.datetime.combine(datetime.date.today(), datetime.time.max),
                    ),
                    settings__cpc_cc__gt=ads["cpc"],
                ).values("settings__cpc_cc")
                if higher_yesterday_cpc:
                    # We skip the sources in which yesterday's CPC was a higher value than the current CPC, it would
                    # produce a false-positive alert because the eCPC will be higher as the old and high value was used.
                    continue
                ads.update(spend)
                alerts.append(ads)
        return alerts
