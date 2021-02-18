import datetime

from core import models
from dash import constants
from utils import k1_helper
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)
OUTBRAIN_SOURCE_ID = 3
DAYS_BACK = 7


class Command(Z1Command):
    help = "Sync ads pending amplify review periodically"

    def handle(self, *args, **options):
        from_date = datetime.date.today() - datetime.timedelta(days=DAYS_BACK)
        content_ads = models.ContentAd.objects.filter(
            id__in=(
                models.ContentAdSource.objects.filter(
                    source_id=OUTBRAIN_SOURCE_ID,
                    submission_status=constants.ContentAdSubmissionStatus.PENDING,
                    created_dt__gte=from_date,
                )
                .select_related("content_ad")
                .distinct("content_ad_id")
                .values_list("content_ad_id", flat=True)
            ),
            archived=False,
            ad_group__campaign__account__amplify_review=True,
        )
        k1_helper.update_content_ads(content_ads, msg="sync_ads_pending_amplify_review")
