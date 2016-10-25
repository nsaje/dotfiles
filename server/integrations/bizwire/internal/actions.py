import pytz

import dash.api
import dash.constants
import dash.models

from . import config

from utils import dates_helper
from utils import k1_helper


def _is_pacific_midnight():
    tz_pacifc = pytz.timezone('America/Los_Angeles')
    pacific_now = dates_helper.utc_to_tz_datetime(dates_helper.utc_now(), tz_pacifc)

    return pacific_now.hour == 0


def check_midnight_and_stop_ads():
    if not _is_pacific_midnight():
        return

    content_ads = dash.models.ContentAd.objects.filter(ad_group_id__in=config.TEST_AD_GROUP_IDS)
    dash.api.update_content_ads_state(content_ads, dash.constants.ContentAdSourceState.INACTIVE, None)
    k1_helper.update_ad_groups(config.TEST_AD_GROUP_IDS)
