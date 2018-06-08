import datetime
from decimal import Decimal
import logging

from utils import dates_helper
from utils import numbers

from .. import RealTimeCampaignDataHistory


import core.multicurrency


logger = logging.getLogger(__name__)

HOURS_DELAY = 6
MAX_RT_DATA_AGE_MINUTES = 15
CHECK_FREQUENCY_MINUTES = 2
MIN_PREV_SPEND_SECONDS = 90


def get_predicted_remaining_budget(log, campaign):
    budget_spends_until_date = _get_until_date_for_budget_spends(campaign)
    current_rt_spends, prev_rt_spends = _get_realtime_spends(
        log, campaign, dates_helper.day_after(budget_spends_until_date))
    available_amount = _get_available_campaign_budget(log, campaign, budget_spends_until_date)

    remaining = available_amount
    if current_rt_spends:
        remaining = available_amount - _sum_rt_spends(current_rt_spends)

    spend_rate_per_minute = _calculate_spend_rate_per_minute(current_rt_spends, prev_rt_spends)
    predicted_spend_increase = spend_rate_per_minute * CHECK_FREQUENCY_MINUTES * 60
    log.add_context({
        'budget_spends_until_date': budget_spends_until_date,
        'available_budget': available_amount,
        'current_rt_spend': _sum_rt_spends(current_rt_spends),
        'prev_rt_spend': _sum_rt_spends(prev_rt_spends),
        'spend_rate': predicted_spend_increase,
    })
    return remaining - predicted_spend_increase


def get_budget_spend_estimates(log, campaign):
    budgets_active_today = _get_budgets_active_today(campaign)
    budget_spend_until_date = _get_until_date_for_budget_spends(campaign)
    current_rt_spend = _get_current_realtime_spend(
        log, campaign, dates_helper.day_after(budget_spend_until_date))

    spend_estimates = {}
    remaining_rt_spend = current_rt_spend if current_rt_spend else 0
    local_remaining_rt_spend = _to_local_currency(campaign, remaining_rt_spend)
    spend_per_budget = {}
    for budget in budgets_active_today:
        past_spend = budget.get_local_spend_data(date=budget_spend_until_date)['etfm_total']
        spend_per_budget[budget.id] = past_spend
        spend_estimates[budget] = min(budget.amount, past_spend + local_remaining_rt_spend)

        rt_added = spend_estimates[budget] - past_spend
        local_remaining_rt_spend -= rt_added

    log.add_context({
        'budget_spends_until_date': budget_spend_until_date,
        'local_spend_per_budget': spend_per_budget,
    })
    return spend_estimates


def _to_local_currency(campaign, amount):
    exchange_rate = core.multicurrency.get_current_exchange_rate(campaign.account.currency)
    return amount * exchange_rate


def _get_current_realtime_spend(log, campaign, start):
    current_rt_spends, _ = _get_realtime_spends(log, campaign, start)
    return _sum_rt_spends(current_rt_spends)


def _sum_rt_spends(rt_spends):
    return sum(s.etfm_spend for s in rt_spends)


def _calculate_spend_rate_per_minute(current_rt_spends, prev_rt_spends):
    if not current_rt_spends or not prev_rt_spends:
        return 0

    # NOTE: for simplicity only compare first element (today's data)
    # because yesterday's data is more likely to be accurate
    seconds_since = ((current_rt_spends[0].created_dt) - (prev_rt_spends[0].created_dt)).total_seconds()

    current_rt_spend = _sum_rt_spends(current_rt_spends)
    prev_rt_spend = _sum_rt_spends(prev_rt_spends)
    rate = (current_rt_spend - prev_rt_spend) / Decimal(seconds_since)
    return numbers.round_decimal_half_down(rate, places=4)


def _get_until_date_for_budget_spends(campaign):
    yesterday = dates_helper.local_yesterday()
    if _should_query_realtime_stats_for_yesterday(campaign):
        return dates_helper.day_before(yesterday)
    return yesterday


def _should_query_realtime_stats_for_yesterday(campaign):
    in_critical_hours = 0 <= dates_helper.local_now().hour < HOURS_DELAY
    local_midnight = dates_helper.local_now().replace(hour=0, minute=0, second=0, microsecond=0)
    local_recent = local_midnight - datetime.timedelta(hours=2)
    utc_recent = dates_helper.local_to_utc_time(local_recent)
    recent_rt_data_exists = RealTimeCampaignDataHistory.objects.filter(
        campaign=campaign,
        date=dates_helper.local_yesterday(),
        created_dt__gte=utc_recent,
    ).exists()  # midnight job that corrects the state for stopped campaigns doesn't have recent yesterday data
    return in_critical_hours and recent_rt_data_exists


def _get_available_campaign_budget(log, campaign, until):
    budgets_active_today = _get_budgets_active_today(campaign)
    log.add_context({'active_budget_line_items': [bli.id for bli in budgets_active_today]})
    return sum(max(bli.get_available_etfm_amount(date=until), 0) for bli in budgets_active_today)


def _get_budgets_active_today(campaign):
    today = dates_helper.local_today()
    return campaign.budgets.filter(
        start_date__lte=today,
        end_date__gte=today,
    ).order_by('created_dt')


def _get_realtime_spends(log, campaign, start):
    tomorrow = dates_helper.day_after(dates_helper.local_today())
    curr_spends, prev_spends = [], []
    for date in dates_helper.date_range(start, tomorrow):
        curr, prev = _get_realtime_spends_for_date(campaign, date)
        if curr:
            curr_spends.append(curr)
        if prev:
            prev_spends.append(prev)

    curr_spends, prev_spends = list(reversed(curr_spends)), list(reversed(prev_spends))
    log.add_context({
        'current_rt_spends_per_date': [(s.date, s.etfm_spend) for s in curr_spends],
        'prev_rt_spends_per_date': [(s.date, s.etfm_spend) for s in prev_spends]
    })
    return curr_spends, prev_spends


def _get_realtime_spends_for_date(campaign, date):
    current_spend = _get_current_spend(campaign, date)
    prev_spend = _get_prev_spend(campaign, date, current_spend)
    if current_spend and not _is_recent(current_spend):
        logger.warning(
            'Real time data is stale. campaign=%s, date=%s',
            campaign,
            date.isoformat()
        )
    return current_spend, prev_spend


def _get_current_spend(campaign, date):
    try:
        return RealTimeCampaignDataHistory.objects.filter(
            date=date,
            campaign=campaign,
        ).latest('created_dt')
    except RealTimeCampaignDataHistory.DoesNotExist:
        return None


def _get_prev_spend(campaign, date, current_spend):
    if not current_spend:
        return None

    max_created_dt = current_spend.created_dt - datetime.timedelta(seconds=MIN_PREV_SPEND_SECONDS)
    try:
        return RealTimeCampaignDataHistory.objects.filter(
            date=date,
            campaign=campaign,
            created_dt__lte=max_created_dt,
        ).exclude(id=current_spend.id).latest('created_dt')
    except RealTimeCampaignDataHistory.DoesNotExist:
        return None


def _is_recent(rt_spend):
    if rt_spend.date != dates_helper.local_today():
        return True
    td = dates_helper.utc_now() - rt_spend.created_dt
    return (td.total_seconds() / 60) < MAX_RT_DATA_AGE_MINUTES
