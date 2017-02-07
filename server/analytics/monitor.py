import logging
import datetime
from decimal import Decimal

from django.db.models import F, Sum

import reports.models
import dash.models
import dash.constants
import automation.models
import analytics.projections
import etl.refresh_k1
from automation import autopilot_helpers
from utils import converters
import redshiftapi.db

logger = logging.getLogger('stats.monitor')

MAX_ERR = 10**7  # 0.01$
SPEND_INTEGRITY_QUERY = """SELECT sum(effective_cost_nano) as media, sum(effective_data_cost_nano) as data, SUM(license_fee_nano) AS fee, SUM(margin_nano) AS margin
FROM {tbl}
WHERE date = '{d}'{additional}
"""

AD_GROUP_SPEND_QUERY = """SELECT ad_group_id
FROM mv_master
WHERE date = '{d}'
GROUP BY ad_group_id
HAVING SUM(effective_cost_nano) >= {threshold}"""

API_ACCOUNTS = (
    293, 305,
)


def _get_rs_spend(table_name, date, account_id=None):
    additional = ''
    if account_id:
        additional = ' AND account_id = {}'.format(account_id)
    with redshiftapi.db.get_stats_cursor() as c:
        c.execute(SPEND_INTEGRITY_QUERY.format(
            tbl=table_name,
            d=str(date),
            additional=additional
        ))
        return redshiftapi.db.dictfetchall(c)[0]
    return {}


def audit_spend_integrity(date, account_id=None):
    if date is None:
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)
    views = [
        tbl for tbl in etl.refresh_k1.NEW_MATERIALIZED_VIEWS
        if tbl.TABLE_NAME.startswith('mv_')
    ]
    spend_queryset = reports.models.BudgetDailyStatement.objects.filter(
        date=date
    )
    if account_id:
        spend_queryset = spend_queryset.filter(budget__campaign__account_id=account_id)
    daily_spend = spend_queryset.values('date').annotate(
        media=Sum(F('media_spend_nano')),
        data=Sum(F('data_spend_nano')),
        margin=Sum(F('margin_nano')),
        fee=Sum(F('license_fee_nano')),
    )[0]
    integrity_issues = []
    for table in views:
        table_name = table.TABLE_NAME

        if 'pubs'in table_name or 'conversions' in table_name or 'touch' in table_name:
            # skip for the first version
            continue
        rs_spend = _get_rs_spend(table_name, date, account_id=account_id)
        for key in rs_spend:
            err = daily_spend[key] - rs_spend[key]
            if abs(err) > MAX_ERR:
                integrity_issues.append((date, table_name, key, err))
    return integrity_issues


def audit_spend_patterns(date=None, threshold=0.8, first_in_month_threshold=0.6, day_range=3):
    if date is None:
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)
    total_spend = Sum(F('media_spend_nano') + F('data_spend_nano') + F('license_fee_nano'))
    result = reports.models.BudgetDailyStatement.objects.filter(
        date__lte=date,
        date__gte=date - datetime.timedelta(day_range),
    ).values('date').annotate(
        total=total_spend
    ).order_by('date')
    totals = [row['total'] for row in result]
    changes = [
        (date + datetime.timedelta(-x), float(totals[-x - 1]) / totals[-x - 2])
        for x in xrange(0, day_range - 1)
    ]
    alarming_dates = [
        (d, change) for d, change in changes
        if d.day == 1 and change < first_in_month_threshold or d.day != 1 and change < threshold
    ]
    return alarming_dates


def audit_pacing(date, max_pacing=Decimal('200.0'), min_pacing=Decimal('50.0'), **constraints):
    if date is None:
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)

    monthly_proj = analytics.projections.CurrentMonthBudgetProjections(
        'campaign',
        date=date,
        **constraints
    )
    alarms = []
    for campaign_id in monthly_proj.keys():
        pacing = monthly_proj.row(campaign_id)['pacing']
        if pacing is None:
            continue
        if pacing > max_pacing:
            alarms.append((campaign_id, pacing, 'high'))
        if pacing < min_pacing:
            alarms.append((campaign_id, pacing, 'low'))
    return alarms


def audit_iab_categories(running_only=False, paused_only=False):
    running_campaign_ids = set(dash.models.AdGroup.objects.all().filter_running().values_list(
        'campaign_id', flat=True
    ))
    campaigns = dash.models.Campaign.objects.all().exclude_archived().exclude(
        account__agency_id__in=(29, )
    )
    if running_only:
        campaigns = campaigns.filter(
            pk__in=running_campaign_ids
        )
    if paused_only:
        campaigns = campaigns.exclude(
            pk__in=running_campaign_ids
        )
    alarms = []
    for campaign in campaigns:
        if campaign.get_current_settings().iab_category == dash.constants.IABCategory.IAB24:
            alarms.append(campaign)
    return alarms


def audit_autopilot_ad_groups():
    date = datetime.date.today()
    ap_logs = automation.models.AutopilotLog.objects.filter(
        created_dt__range=(datetime.datetime.combine(date, datetime.time.min),
                           datetime.datetime.combine(date, datetime.time.max)),
        is_autopilot_job_run=True
    )
    ad_groups_in_logs = set(log.ad_group for log in ap_logs)
    ad_groups_ap_running = set(autopilot_helpers.get_active_ad_groups_on_autopilot()[0])
    return ad_groups_ap_running - ad_groups_in_logs


def audit_autopilot_cpc_changes(date=None, min_changes=25):
    if not date:
        date = datetime.date.today()
    ap_logs = automation.models.AutopilotLog.objects.filter(
        created_dt__range=(datetime.datetime.combine(date, datetime.time.min),
                           datetime.datetime.combine(date, datetime.time.max)),
        is_autopilot_job_run=True,
        ad_group_source__source__deprecated=False,
        ad_group_source__source__maintenance=False
    )
    source_changes = {}
    for log in ap_logs:
        source_changes.setdefault(
            log.ad_group_source.source,
            []
        ).append(log.new_cpc_cc - log.previous_cpc_cc)
    alarms = {}
    for source, changes in source_changes.iteritems():
        if len(changes) < min_changes:
            continue
        positive_changes = filter(lambda x: x >= 0, changes)
        negative_changes = filter(lambda x: x <= 0, changes)
        if len(positive_changes) == len(changes):
            alarms[source] = sum(positive_changes)
        if len(negative_changes) == len(changes):
            alarms[source] = sum(negative_changes)
    return alarms


def audit_autopilot_budget_totals(date=None, error=Decimal('0.001')):
    if not date:
        date = datetime.date.today()
    alarms = {}
    state = dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
    ad_groups, ad_groups_settings = autopilot_helpers.get_active_ad_groups_on_autopilot(state)
    ad_group_sources_settings = autopilot_helpers.get_autopilot_active_sources_settings(ad_groups)
    for settings in ad_groups_settings:
        total_ap_budget = Decimal(0)
        filtered_source_settings = filter(
            lambda agss: agss.ad_group_source.ad_group_id == settings.ad_group_id,
            ad_group_sources_settings
        )
        for source_settings in filtered_source_settings:
            total_ap_budget += source_settings.daily_budget_cc
        if abs(settings.autopilot_daily_budget - total_ap_budget) >= error:
            alarms[settings.ad_group] = settings.autopilot_daily_budget - total_ap_budget
    return alarms


def audit_autopilot_budget_changes(date=None, error=Decimal('0.001')):
    if not date:
        date = datetime.date.today()
    ap_logs = automation.models.AutopilotLog.objects.filter(
        created_dt__range=(datetime.datetime.combine(date, datetime.time.min),
                           datetime.datetime.combine(date, datetime.time.max)),
        is_autopilot_job_run=True,
        ad_group_source__source__deprecated=False,
        ad_group_source__source__maintenance=False
    ).exclude(
        ad_group__in=dash.models.AdGroup.objects.all().filter_landing(),
    )
    total_changes = {}
    for log in ap_logs:
        total_changes.setdefault(
            log.ad_group,
            []
        ).append(log.new_daily_budget - log.previous_daily_budget)
    alarms = {}
    for ad_group, changes in total_changes.iteritems():
        budget_changes = sum(changes)
        if abs(budget_changes) > error:
            alarms[ad_group] = budget_changes
    return alarms


def audit_running_ad_groups(min_spend=Decimal('50.0')):
    """
    Audit ad groups spend of non API active ad groups of types:
    - PILOT
    - ACTIVATED
    - MANAGED
    """
    yesterday = datetime.date.today() - datetime.timedelta(1)
    running_ad_group_ids = set(dash.models.AdGroup.objects.all().filter_running(
        date=yesterday
    ).filter_by_account_types((
        dash.constants.AccountType.PILOT,
        dash.constants.AccountType.ACTIVATED,
        dash.constants.AccountType.MANAGED,
    )).values_list(
        'pk', flat=True
    ))
    api_ad_groups = set(dash.models.AdGroup.objects.filter(
        campaign__account_id__in=API_ACCOUNTS
    ).values_list(
        'pk', flat=True
    ))

    with redshiftapi.db.get_stats_cursor() as c:
        c.execute(AD_GROUP_SPEND_QUERY.format(
            d=str(yesterday),
            threshold=str(int(min_spend * converters.DOLAR_TO_NANO))
        ))
        spending_ad_group_ids = set(int(row[0]) for row in c.fetchall())
    return dash.models.AdGroup.objects.filter(
        pk__in=((running_ad_group_ids - spending_ad_group_ids) - api_ad_groups)
    )
