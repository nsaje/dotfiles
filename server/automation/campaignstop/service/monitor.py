import datetime

from .. import constants
from .. import RealTimeCampaignStopLog

from utils import dates_helper


def audit_stopped_campaigns(date):
    local_midnight = dates_helper.local_to_utc_time(datetime.datetime(date.year, date.month, date.day))
    logs = RealTimeCampaignStopLog.objects.filter(
        created_dt__gte=local_midnight,
        created_dt__lt=dates_helper.day_after(local_midnight),
        context__previous_state=constants.CampaignStopState.ACTIVE,
        context__new_state=constants.CampaignStopState.STOPPED,
    )
    campaigns = set(log.campaign for log in logs)
    return {
        campaign: _get_available_campaign_budget(campaign) for campaign in campaigns
    }


def _get_available_campaign_budget(campaign):
    budgets_active_today = _get_budgets_active_today(campaign)
    return sum(bli.get_available_etfm_amount() for bli in budgets_active_today)


def _get_budgets_active_today(campaign):
    today = dates_helper.local_today()
    return campaign.budgets.filter(
        start_date__lte=today,
        end_date__gte=today,
    ).order_by('created_dt')
