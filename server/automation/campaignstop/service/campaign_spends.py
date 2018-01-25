from utils import dates_helper

from .. import RealTimeCampaignDataHistory

HOURS_DELAY = 6


def get_predicted_remaining_budget(log, campaign):
    budget_spends_until_date = _get_until_date_for_budget_spends(campaign)
    current_rt_spend, prev_rt_spend = _get_realtime_spends(
        log, campaign, dates_helper.day_after(budget_spends_until_date))
    available_amount = _get_available_campaign_budget(campaign, budget_spends_until_date)

    remaining = available_amount
    if current_rt_spend:
        remaining = available_amount - current_rt_spend

    spend_rate = _calculate_spend_rate(current_rt_spend, prev_rt_spend)
    log.add_context({
        'budget_spends_until_date': budget_spends_until_date,
        'available_budget': available_amount,
        'current_rt_spend': current_rt_spend,
        'prev_rt_spend': prev_rt_spend,
        'spend_rate': spend_rate,
    })
    return remaining - spend_rate


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
    current_rt_spend, _ = _get_realtime_spends(log, campaign, start)
    return current_rt_spend


def _calculate_spend_rate(current_rt_spend, prev_rt_spend):
    if current_rt_spend is None or prev_rt_spend is None:
        return 0

    return current_rt_spend - prev_rt_spend


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
    return sum(bli.get_available_etfm_amount(date=until) for bli in budgets_active_today)


def _get_budgets_active_today(campaign):
    today = dates_helper.local_today()
    return campaign.budgets.filter(
        start_date__lte=today,
        end_date__gte=today,
    ).order_by('created_dt')


def _get_realtime_spends(log, campaign, start):
    tomorrow = dates_helper.day_after(dates_helper.local_today())
    current_spend, prev_spend = None, None
    current_spends_per_date = []
    prev_spends_per_date = []
    for date in dates_helper.date_range(start, tomorrow):
        curr, prev = _get_realtime_spends_for_date(campaign, date)
        current_spends_per_date.append((date, curr))
        prev_spends_per_date.append((date, prev))
        current_spend = current_spend + curr if current_spend else curr
        prev_spend = prev_spend + prev if prev_spend else prev
    log.add_context({
        'current_rt_spends_per_date': current_spends_per_date,
        'prev_rt_spends_per_date': prev_spends_per_date
    })
    return current_spend, prev_spend


def _get_realtime_spends_for_date(campaign, date):
    spends = list(
        RealTimeCampaignDataHistory.objects.filter(
            date=date,
            campaign=campaign,
        ).order_by('-created_dt')[:2]
    )

    current_spend, prev_spend = None, None
    if len(spends) > 0:
        current_spend = spends[0].etfm_spend
    if len(spends) > 1:
        prev_spend = spends[1].etfm_spend

    return current_spend, prev_spend
