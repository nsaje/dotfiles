from core import models
from dash import constants
from utils import k1_helper
from utils import zlogging
from utils.command_helpers import Z1Command
from utils.dates_helper import utc_yesterday

logger = zlogging.getLogger(__name__)
OUTBRAIN_SOURCE_ID = 3


class Command(Z1Command):
    help = "Sync ads pending amplify review periodically"

    def handle(self, *args, **options):
        yesterday = utc_yesterday()
        content_ads = models.ContentAd.objects.filter(
            id__in=(
                models.ContentAdSource.objects.filter(
                    source_id=OUTBRAIN_SOURCE_ID,
                    submission_status=constants.ContentAdSubmissionStatus.PENDING,
                    created_dt__gte=yesterday,
                )
                .select_related("content_ad")
                .distinct("content_ad_id")
                .values_list("content_ad_id", flat=True)
            ),
            archived=False,
            ad_group__campaign__account__amplify_review=True,
        )
        k1_helper.update_content_ads(content_ads, msg="sync_ads_pending_amplify_review")
