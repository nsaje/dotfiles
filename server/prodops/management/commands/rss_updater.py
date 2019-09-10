import datetime

import core.models
import dash.constants
from utils.command_helpers import Z1Command

AD_GROUPS = {
    873888,
    873885,
    885222,
    885223,
    885904,
    885905,
    885906,
    885907,
    885908,
    885909,
    885910,
    888572,
    712843,
    885024,
    885025,
    885026,
    885039,
    885015,
    885036,
    885037,
    885027,
    885040,
    885143,
    888574,
    883634,
    883643,
    883608,
    883635,
    883676,
    883675,
    883661,
    888569,
    883376,
    883377,
    883378,
    883397,
    883379,
    883380,
    883381,
    883409,
    883429,
    883074,
    883078,
    883077,
    883082,
    883079,
    883086,
    883087,
    883089,
    883090,
    886804,
    886805,
    886806,
}
DAYS_TTL = 3


class Command(Z1Command):
    def handle(self, *args, **options):
        for ad in core.models.ContentAd.objects.filter(ad_group__id__in=AD_GROUPS):
            if not ad.state == dash.constants.ContentAdSourceState.ACTIVE:
                continue
            elif ad.created_dt < (datetime.datetime.today() - datetime.timedelta(DAYS_TTL)):
                ad.set_state(None, dash.constants.ContentAdSourceState.INACTIVE)
