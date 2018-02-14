import datetime

from .. import constants
from .. import RealTimeCampaignStopLog

from utils import dates_helper


def audit_stopped_campaigns(date):
    local_midnight = dates_helper.utc_to_local(datetime.datetime(date.year, date.month, date.day))
    logs = RealTimeCampaignStopLog.objects.filter(
        created_dt__gte=local_midnight,
        created_dt__lt=dates_helper.day_after(local_midnight),
        context__previous_state=constants.CampaignStopState.ACTIVE,
        context__new_state=constants.CampaignStopState.STOPPED,
    )
    campaigns = set(log.campaign for log in logs)
    return sorted(campaigns, key=lambda x: x.id)
