from decimal import Decimal
import logging

from utils import dates_helper
from utils import numbers

from .. import RealTimeCampaignDataHistory


logger = logging.getLogger(__name__)

HOURS_DELAY = 6
MAX_RT_DATA_AGE_MINUTES = 15
CHECK_FREQUENCY_MINUTES = 5


def get_predicted_remaining_budget(log, campaign):
    budget_spends_until_date = _get_until_date_for_budget_spends(campaign)
    current_rt_spends, prev_rt_spends = _get_realtime_spends(
        log, campaign, dates_helper.day_after(budget_spends_until_date))
    available_amount = _get_available_campaign_budget(campaign, budget_spends_until_date)

    remaining = available_amount
    if current_rt_spends:
        remaining = available_amount - _sum_rt_spends(current_rt_spends)

    spend_rate = _calculate_spend_rate(current_rt_spends, prev_rt_spends)
    predicted_sped_increase = spend_rate * CHECK_FREQUENCY_MINUTES * 60
    log.add_context({
        'budget_spends_until_date': budget_spends_until_date,
        'available_budget': available_amount,
        'current_rt_spend': _sum_rt_spends(current_rt_spends),
        'prev_rt_spend': _sum_rt_spends(prev_rt_spends),
        'spend_rate': predicted_sped_increase,
    })
    return remaining - predicted_sped_increase


def get_budget_spend_estimates(log, campaign):
    budgets_active_today = _get_budgets_active_today(campaign)
    budget_spend_until_date = _get_until_date_for_budget_spends(campaign)
    current_rt_spend = _get_current_realtime_spend(
        log, campaign, dates_helper.day_after(budget_spend_until_date))

    spend_estimates = {}
    remaining_rt_spend = current_rt_spend if current_rt_spend else 0
    for budget in budgets_active_today:
        past_spend = budget.get_spend_data(date=budget_spend_until_date)['etfm_total']
        spend_estimates[budget] = min(budget.amount, past_spend + remaining_rt_spend)

        rt_added = spend_estimates[budget] - past_spend
        remaining_rt_spend -= rt_added

    return spend_estimates


def _get_current_realtime_spend(log, campaign, start):
    current_rt_spends, _ = _get_realtime_spends(log, campaign, start)
    return _sum_rt_spends(current_rt_spends)


def _sum_rt_spends(rt_spends):
    return sum(s.etfm_spend for s in rt_spends)


def _calculate_spend_rate(current_rt_spends, prev_rt_spends):
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
    if _should_query_realtime_stats_for_yesterday(campaign, yesterday):
        return dates_helper.day_before(yesterday)
    return yesterday


def _should_query_realtime_stats_for_yesterday(campaign, date):
    in_critical_hours = 0 <= dates_helper.local_now().hour < HOURS_DELAY
    return in_critical_hours


def _get_available_campaign_budget(campaign, until):
    budgets_active_today = _get_budgets_active_today(campaign)
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

    log.add_context({
        'current_rt_spends_per_date': [(s.date, s.etfm_spend) for s in curr_spends],
        'prev_rt_spends_per_date': [(s.date, s.etfm_spend) for s in prev_spends]
    })
    return curr_spends, prev_spends


def _get_realtime_spends_for_date(campaign, date):
    spends = list(
        RealTimeCampaignDataHistory.objects.filter(
            date=date,
            campaign=campaign,
        ).order_by('-created_dt')[:2]
    )

    current_spend, prev_spend = None, None
    if len(spends) > 0:
        if not _is_recent(spends[0]):
            logger.warning(
                'Real time data is stale. campaign=%s, date=%s',
                campaign,
                date.isoformat()
            )
        current_spend = spends[0]
    if len(spends) > 1:
        prev_spend = spends[1]

    return current_spend, prev_spend


def _is_recent(rt_spend):
    td = dates_helper.utc_now() - rt_spend.created_dt
    return (td.total_seconds() / 60) < MAX_RT_DATA_AGE_MINUTES
