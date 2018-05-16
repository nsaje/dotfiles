import logging
import datetime
from decimal import Decimal

from django.db.models import F, Sum

import dash.models
import dash.constants
import automation.models
import analytics.projections
import etl.refresh_k1
from automation import autopilot
from utils import converters
import redshiftapi.db
import analytics.helpers

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

CLICK_DISCREPANCY_QUERY = """SELECT campaign_id, (CASE
  WHEN SUM(clicks) = 0 THEN NULL
  WHEN SUM(visits) = 0 THEN 1
  WHEN SUM(clicks) < SUM(visits) THEN 0
  ELSE (SUM(CAST(clicks AS FLOAT)) - SUM(visits)) / SUM(clicks) END)*100.0 cd
FROM mv_master
WHERE date >= '{from_date}' AND date <= '{till_date}' AND campaign_id IN ({campaigns})
GROUP BY campaign_id"""

OVERSPEND_QUERY = """SELECT account_id,
       (sum(cost_nano) - sum(effective_cost_nano)) +
       (sum(data_cost_nano) - sum(effective_data_cost_nano)) as diff
FROM mv_account
WHERE date = '{date}'
GROUP BY account_id
HAVING sum(cost_nano) - sum(effective_cost_nano) > {threshold} or
       sum(data_cost_nano) - sum(effective_data_cost_nano) > {threshold}
"""

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


def audit_spend_integrity(date, account_id=None, max_err=MAX_ERR):
    if date is None:
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)
    spend_queryset = dash.models.BudgetDailyStatement.objects.filter(
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
    for table_name in etl.refresh_k1.get_all_views_table_names():

        if 'pubs'in table_name or 'conversions' in table_name or 'touch' in table_name:
            # skip for the first version
            continue
        if table_name.endswith('_conv'):
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
    total_spend = Sum(F('media_spend_nano') + F('data_spend_nano') + F('license_fee_nano'))
    result = dash.models.BudgetDailyStatement.objects.filter(
        date__lte=date,
        date__gte=date - datetime.timedelta(day_range),
    ).values('date').annotate(
        total=total_spend
    ).order_by('date')
    totals = [row['total'] for row in result]
    changes = [
        (date + datetime.timedelta(-x), float(totals[-x - 1]) / totals[-x - 2])
        for x in range(0, day_range - 1)
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
    for campaign_id in list(monthly_proj.keys()):
        pacing = monthly_proj.row(campaign_id)['pacing']
        if pacing is None:
            continue
        if pacing > max_pacing:
            alarms.append((campaign_id, pacing, 'high', monthly_proj.row(campaign_id)))
        if pacing < min_pacing:
            alarms.append((campaign_id, pacing, 'low', monthly_proj.row(campaign_id)))
    return alarms


def audit_autopilot_ad_groups():
    date = datetime.date.today()
    ap_logs = automation.models.AutopilotLog.objects.filter(
        created_dt__range=(datetime.datetime.combine(date, datetime.time.min),
                           datetime.datetime.combine(date, datetime.time.max)),
        is_autopilot_job_run=True
    )
    ad_groups_in_logs = set(log.ad_group for log in ap_logs)
    ad_groups_ap_running = set(autopilot.helpers.get_active_ad_groups_on_autopilot()[0])
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


def audit_autopilot_budget_totals(date=None, error=Decimal('0.001')):
    if not date:
        date = datetime.date.today()
    alarms = {}
    state = dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
    ad_groups, ad_groups_settings = autopilot.helpers.get_active_ad_groups_on_autopilot(state)
    ad_group_sources_settings = autopilot.helpers.get_autopilot_active_sources_settings({
        ags.ad_group: ags for ags in ad_groups_settings
    })
    for settings in ad_groups_settings:
        total_ap_budget = Decimal(0)
        filtered_source_settings = [agss for agss in ad_group_sources_settings if agss.ad_group_source.ad_group_id == settings.ad_group_id]
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
        ad_group_source__source__maintenance=False,
        autopilot_type=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
    ).exclude(
        ad_group__in=dash.models.AdGroup.objects.all().filter_landing(),
    )
    total_changes = {}
    for log in ap_logs:
        if not log.new_daily_budget or not log.previous_daily_budget:
            continue
        total_changes.setdefault(
            log.ad_group,
            []
        ).append(log.new_daily_budget - log.previous_daily_budget)
    alarms = {}
    for ad_group, changes in total_changes.items():
        budget_changes = sum(changes)
        if not budget_changes or abs(budget_changes) > error:
            alarms[ad_group] = budget_changes
    return alarms


def audit_overspend(date, min_overspend=Decimal('0.1')):
    rows = redshiftapi.db.execute_query(
        OVERSPEND_QUERY.format(
            date=str(date),
            threshold=str(int(min_overspend * converters.CURRENCY_TO_NANO))
        ),
        [],
        'audit_overspend',
    )
    accounts_map = {
        account.id: account for account in dash.models.Account.objects.all()
    }
    alarms = {}
    for row in rows:
        account = accounts_map[row['account_id']]
        alarms[account] = converters.nano_to_decimal(row['diff'])
    return alarms


def audit_running_ad_groups(min_spend=Decimal('50.0'), account_types=None):
    """
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
    running_ad_group_ids = set(dash.models.AdGroup.objects.all().filter_running(
        date=yesterday
    ).filter_by_account_types(account_types).values_list(
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
            threshold=str(int(min_spend * converters.CURRENCY_TO_NANO))
        ))
        spending_ad_group_ids = set(int(row[0]) for row in c.fetchall())
    return dash.models.AdGroup.objects.filter(
        pk__in=((running_ad_group_ids - spending_ad_group_ids) - api_ad_groups)
    )


def audit_account_credits(date=None, days=14):
    if not date:
        date = datetime.date.today()
    ending_credit_accounts = set(
        credit.account or credit.agency.account_set.all().first()
        for credit in dash.models.CreditLineItem.objects.filter(
            end_date__gte=date,
            end_date__lt=date + datetime.timedelta(days)
        )
    )
    future_credit_accounts = set(
        credit.account or credit.agency.account_set.all().first()
        for credit in dash.models.CreditLineItem.objects.filter(
            end_date__gte=date + datetime.timedelta(days)
        )
    )
    return ending_credit_accounts - future_credit_accounts


def audit_click_discrepancy(date=None, days=30, threshold=20):
    if date is None:
        date = datetime.date.today() - datetime.timedelta(1)
    from_date = date - datetime.timedelta(days + 1)
    till_date = date - datetime.timedelta(1)

    campaigns = {
        c.pk: c for c in dash.models.Campaign.objects.filter(
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
            ).values_list('campaign_id', flat=True)
        )
    }

    data_base, data_test = {}, {}
    with redshiftapi.db.get_stats_cursor() as c:
        c.execute(CLICK_DISCREPANCY_QUERY.format(
            campaigns=','.join(map(str, list(campaigns.keys()))),
            from_date=from_date,
            till_date=till_date,
        ))
        data_base = {int(r[0]): r[1] for r in c.fetchall()}
        c.execute(CLICK_DISCREPANCY_QUERY.format(
            campaigns=','.join(map(str, list(campaigns.keys()))),
            from_date=date,
            till_date=date,
        ))
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


def audit_custom_hacks(minimal_spend=Decimal('0.0001')):
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
            agency=unconfirmed_hack.agency
        )
        if not spend or ((spend[0]['media'] or Decimal('0')) + (spend[0]['data'] or Decimal('0'))) < minimal_spend:
            continue
        alarms.append((
            unconfirmed_hack,
            'media: ${media}, data: ${data}, fee: ${fee}, margin: ${margin}'.format(**spend[0]),
        ))
    return alarms
