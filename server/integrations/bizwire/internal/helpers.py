import pytz
from utils import dates_helper

from integrations.bizwire import config, models


def get_pacific_now():
    tz_pacifc = pytz.timezone('America/Los_Angeles')
    return dates_helper.utc_to_tz_datetime(dates_helper.utc_now(), tz_pacifc)


def get_current_ad_group_id():
    today = get_pacific_now().date()
    return models.AdGroupRotation.objects.filter(
        ad_group__campaign_id=config.AUTOMATION_CAMPAIGN,
        start_date__lte=today
    ).latest('start_date').ad_group_id
