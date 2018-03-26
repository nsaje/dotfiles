import datetime
import decimal

from .. import constants
from .. import RealTimeCampaignStopLog

from redshiftapi import db

from utils import dates_helper
from utils import converters
from utils import numbers


def audit_stopped_campaigns(date):
    local_midnight = dates_helper.local_to_utc_time(datetime.datetime(date.year, date.month, date.day))
    logs = RealTimeCampaignStopLog.objects.filter(
        created_dt__gte=local_midnight,
        created_dt__lt=dates_helper.day_after(local_midnight),
        context__previous_state=constants.CampaignStopState.ACTIVE,
        context__new_state=constants.CampaignStopState.STOPPED,
    ).order_by('campaign_id', '-created_dt').distinct('campaign')
    return {
        log.campaign: _get_available_campaign_budget(date, log) for log in logs
    }


def _get_available_campaign_budget(date, log):
    budgets_active_today = _get_budgets_active_today(date, log)
    available = None
    active_budgets = False
    if budgets_active_today:
        available = sum(bli.get_available_etfm_amount() for bli in budgets_active_today)
        available = numbers.round_decimal_half_down(decimal.Decimal(available), places=2)
        active_budgets = True

    return {
        'available': available,
        'active_budgets': active_budgets,
        'overspend': _get_overspend(date, log),
    }


def _get_overspend(date, log):
    db.execute_query(
        'select ((sum(cost_nano) + sum(data_cost_nano)) - (sum(effective_cost_nano) + sum(effective_data_cost_nano))) / 1000000000.0 from mv_campaign where campaign_id = %s and date=%s',
        [date, log.campaign.id],
        'campaignstop_monitor_overspend'
    )


def _get_budgets_active_today(date, log):
    budgets = log.campaign.budgets.all()
    if 'active_budget_line_items' not in log.context:
        budgets = budgets.filter(
            start_date__lte=date,
            end_date__gte=dates_helper.days_before(date, 2),  # budgets that ended 2 days ago were stopped yesterday
        )
    elif not log.context['active_budget_line_items']:
        budgets = budgets.none()
    else:
        active_items = log.context['active_budget_line_items']
        if not isinstance(active_items, list):
            active_items = [active_items]
        budgets = budgets.filter(
            id__in=active_items,
        )
    return budgets.order_by('created_dt')
