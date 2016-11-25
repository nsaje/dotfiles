import pytz
from utils import dates_helper


def get_pacific_now():
    tz_pacifc = pytz.timezone('America/Los_Angeles')
    return dates_helper.utc_to_tz_datetime(dates_helper.utc_now(), tz_pacifc)
