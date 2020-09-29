from django.db import connection
from django.db import transaction

import automation.campaignstop
import utils.dates_helper
from utils import metrics_compat
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


REALTIME_DATA_KEEP_DAYS = 7


class Command(Z1Command):
    @metrics_compat.timer("campaignstop.job_run", campaignstop_job="clean_up")
    def handle(self, *args, **options):
        logger.info("Start: deleting old realtime campaign stop data")
        self._delete_old_data()
        logger.info("Finish: old campaign stop realtime data deleted and tables vacuumed/analyzed")

    @staticmethod
    def _delete_old_data():
        date_to = utils.dates_helper.days_before(utils.dates_helper.local_today(), REALTIME_DATA_KEEP_DAYS)

        with transaction.atomic():
            automation.campaignstop.RealTimeCampaignDataHistory.objects.filter(date__lt=date_to).delete()
            automation.campaignstop.RealTimeDataHistory.objects.filter(date__lt=date_to).delete()

        with connection.cursor() as cursor:
            cursor.execute("VACUUM ANALYZE automation_realtimecampaigndatahistory;")
            cursor.execute("VACUUM ANALYZE automation_realtimedatahistory;")
