import decimal

from django.db import transaction

import core.entity
from utils import dates_helper

from ..constants import CampaignStopEvent
from .. import RealTimeCampaignStopLog, CampaignStopState, RealTimeCampaignDataHistory

THRESHOLD = decimal.Decimal('10')
HOURS_DELAY = 6


def update_campaigns_state(campaigns=None):
    if not campaigns:
        campaigns = core.entity.Campaign.objects.all()
    _update_campaigns(campaign for campaign in campaigns if campaign.real_time_campaign_stop)


def _update_campaigns(campaigns):
    for campaign in campaigns:
        _update_campaign(campaign)


@transaction.atomic
def _update_campaign(campaign):
    campaign_state, _ = CampaignStopState.objects.get_or_create(campaign=campaign)
    log = RealTimeCampaignStopLog(
        campaign=campaign, event=CampaignStopEvent.BUDGET_DEPLETION_CHECK)
    campaign_state.set_allowed_to_run(_is_allowed_to_run(log, campaign, campaign_state))


def _is_allowed_to_run(log, campaign, campaign_state):
    allowed_to_run = (
        not _is_max_end_date_past(log, campaign, campaign_state) and
        not _is_below_threshold(log, campaign)
    )
    log.add_context({'allowed_to_run': allowed_to_run})
    return allowed_to_run


def _is_max_end_date_past(log, campaign, campaign_state):
    is_past = (
        campaign_state.max_allowed_end_date and
        campaign_state.max_allowed_end_date < dates_helper.local_today()
    )
    log.add_context({
        'max_allowed_end_date': campaign_state.max_allowed_end_date,
        'is_max_end_date_past': is_past,
    })
    return is_past


def _is_below_threshold(log, campaign):
    budget_spends_until_date = _get_until_date_for_budget_spends(campaign)
    available_budget = _get_available_campaign_budget(
        campaign, budget_spends_until_date)
    current_rt_spend, prev_rt_spend = _get_realtime_spends(
        log, campaign, dates_helper.day_after(budget_spends_until_date))

    remaining = available_budget
    if current_rt_spend:
        remaining -= current_rt_spend

    spend_rate = 0
    if current_rt_spend and prev_rt_spend:
        spend_rate = current_rt_spend - prev_rt_spend

    predicted = remaining - spend_rate
    is_below = predicted < THRESHOLD
    log.add_context({
        'budget_spends_until_date': budget_spends_until_date,
        'available_budget': available_budget,
        'current_rt_spend': current_rt_spend,
        'prev_rt_spend': prev_rt_spend,
        'spend_rate': spend_rate,
        'predicted': predicted,
        'is_below_threshold': is_below,
    })
    return is_below


def _get_until_date_for_budget_spends(campaign):
    yesterday = dates_helper.local_yesterday()
    if _should_query_realtime_stats_for_yesterday(campaign, yesterday):
        return dates_helper.day_before(yesterday)
    return yesterday


def _should_query_realtime_stats_for_yesterday(campaign, date):
    history_entries = RealTimeCampaignDataHistory.objects.filter(
        campaign=campaign, date=dates_helper.local_yesterday())
    in_critical_hours = 0 <= dates_helper.local_now().hour < HOURS_DELAY
    return in_critical_hours and history_entries.exists()


def _get_available_campaign_budget(campaign, until):
    today = dates_helper.local_today()
    budgets_active_today = campaign.budgets.filter(
        start_date__lte=today,
        end_date__gte=today,
    ).select_related('credit')
    return sum(bli.get_available_etfm_amount(date=until) for bli in budgets_active_today)


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
