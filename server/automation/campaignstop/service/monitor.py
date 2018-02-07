from .. import RealTimeCampaignStopLog

from utils import dates_helper


def audit_stopped_campaigns(date):
    next_day = dates_helper.day_after(date)
    logs = RealTimeCampaignStopLog.objects.filter(
        created_dt__gte=date, created_dt__lt=next_day, context__allowed_to_run=False)
    campaigns = set(log.campaign for log in logs)
    return campaigns
