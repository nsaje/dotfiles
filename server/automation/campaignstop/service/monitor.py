from .. import constants
from .. import RealTimeCampaignStopLog

from utils import dates_helper


def audit_stopped_campaigns(date):
    next_day = dates_helper.day_after(date)
    logs = RealTimeCampaignStopLog.objects.filter(
        created_dt__gte=date, created_dt__lt=next_day,
        context__previous_state=constants.CampaignStopState.ACTIVE,
        context__new_state=constants.CampaignStopState.STOPPED,
    )
    campaigns = set(log.campaign for log in logs)
    return campaigns
