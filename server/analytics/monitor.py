import logging
import datetime
from decimal import Decimal

from django.db.models import F, Sum

import reports.models
import dash.models
import dash.constants
import analytics.projections
import etl.refresh_k1

import redshiftapi.db

logger = logging.getLogger('stats.monitor')

MAX_ERR = 10**7  # 0.01$
SPEND_INTEGRITY_QUERY = """SELECT sum(effective_cost_nano) as media, sum(effective_data_cost_nano) as data, SUM(license_fee_nano) AS fee, SUM(margin_nano) AS margin
FROM {tbl}
WHERE date = '{d}'{additional}
"""


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
    campaigns = dash.models.Campaign.objects.all().exclude_archived()
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
