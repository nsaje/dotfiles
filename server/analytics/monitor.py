import datetime
from decimal import Decimal

from django.conf import settings
from django.db.models import F
from django.db.models import Sum

import automation.models
import backtosql
import dash.constants
import dash.models
import etl.refresh
import redshiftapi.db
from automation import autopilot
from automation import autopilot_legacy
from utils import zlogging

logger = zlogging.getLogger("stats.monitor")

MAX_ERR = 10 ** 9  # 0.0001$

API_ACCOUNTS = (settings.HARDCODED_ACCOUNT_ID_BUSINESSWIRE, settings.HARDCODED_ACCOUNT_ID_OEN)


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
    daily_spend = (
        spend_queryset.values("date")
        .annotate(
            base_media=Sum(F("base_media_spend_nano")),
            base_data=Sum(F("base_data_spend_nano")),
            service_fee=Sum(F("service_fee_nano")),
            license_fee=Sum(F("license_fee_nano")),
            margin=Sum(F("margin_nano")),
        )
        .first()
    )
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


def audit_autopilot_ad_groups():
    date = datetime.date.today()
    ad_groups_ids_in_logs = set(
        automation.models.AutopilotLog.objects.filter(
            created_dt__range=(
                datetime.datetime.combine(date, datetime.time.min),
                datetime.datetime.combine(date, datetime.time.max),
            ),
            is_autopilot_job_run=True,
            ad_group__created_dt__lt=date,
        ).values_list("id", flat=True)
    )
    ad_groups_ap_running = set(
        autopilot.helpers.get_active_ad_groups_on_autopilot()
        .filter(created_dt__lt=datetime.datetime.combine(date, datetime.time.min))
        .values_list("id", flat=True)
    )

    # TODO: RTAP: LEGACY
    ad_groups_ap_running_legacy = set(
        autopilot_legacy.helpers.get_active_ad_groups_on_autopilot()
        .filter(created_dt__lt=datetime.datetime.combine(date, datetime.time.min))
        .values_list("id", flat=True)
    )

    return dash.models.AdGroup.objects.filter(
        id__in=set((ad_groups_ap_running | ad_groups_ap_running_legacy) - ad_groups_ids_in_logs)
    )


# TODO: RTAP: LEGACY: remove after all migrated (can we do it now already?)
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


# TODO: RTAP: LEGACY: remove after all migrated (can we do it now already?)
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


def audit_account_credits(date=None, days=14):

    if not date:
        date = datetime.date.today()
    ending_credit_accounts = set(
        credit.account or credit.agency.account_set.all().first()
        for credit in dash.models.CreditLineItem.objects.filter(
            end_date__gte=date, end_date__lt=date + datetime.timedelta(days)
        ).prefetch_related("agency__account_set")
        if credit.account or credit.agency.account_set.all()
    )
    future_credit_accounts = set(
        credit.account or credit.agency.account_set.all().first()
        for credit in dash.models.CreditLineItem.objects.filter(
            end_date__gte=date + datetime.timedelta(days)
        ).prefetch_related("agency__account_set")
        if credit.account or credit.agency.account_set.all()
    )
    # only accounts with no future credits
    return ending_credit_accounts - future_credit_accounts
