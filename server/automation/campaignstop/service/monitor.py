import datetime

from .. import constants
from .. import RealTimeCampaignStopLog

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
        log.campaign: _get_available_campaign_budget(log) for log in logs
    }


def _get_available_campaign_budget(log):
    budgets_active_today = _get_budgets_active_today(log)
    freed = sum(bli.freed_cc for bli in budgets_active_today) * converters.CC_TO_DECIMAL_DOLAR
    available = sum(bli.get_available_etfm_amount() for bli in budgets_active_today)
    return {
        'available': numbers.round_decimal_half_down(available + freed, places=2),
        'freed': numbers.round_decimal_half_down(freed, places=2),
    }


def _get_budgets_active_today(log):
    today = dates_helper.local_today()
    budgets = log.campaign.budgets.all()
    if 'active_budget_line_items' in log.context:
        active_items = log.context['active_budget_line_items']
        if not isinstance(active_items, list):
            active_items = [active_items]
        budgets = budgets.filter(
            id__in=active_items,
        )
    else:
        budgets = budgets.filter(
            start_date__lte=today,
            end_date__gte=dates_helper.local_yesterday(),
        )
    return budgets.order_by('created_dt')
