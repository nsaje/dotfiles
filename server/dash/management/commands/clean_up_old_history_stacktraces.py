from django.db import transaction

import core.features.history.models
import utils.dates_helper
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


HISTORY_DATA_KEEP_DAYS = 14


class Command(Z1Command):
    def handle(self, *args, **options):
        logger.info("Start: deleting old history stacktraces")
        self._delete_old_data()
        logger.info("Finish: deleted old history stacktraces")

    @staticmethod
    def _delete_old_data():
        date_to = utils.dates_helper.days_before(utils.dates_helper.local_today(), HISTORY_DATA_KEEP_DAYS)

        with transaction.atomic():
            core.features.history.models.HistoryStacktrace.objects.filter(created_dt__lte=date_to).delete()
