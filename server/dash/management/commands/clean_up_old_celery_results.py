import django_celery_results.models
import utils.dates_helper
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


CELERY_RESULTS_DATA_KEEP_DAYS = 30


class Command(Z1Command):
    def handle(self, *args, **options):
        logger.info("Start: deleting old Celery results")
        self._delete_old_data()
        logger.info("Finish: deleted old Celery results")

    @staticmethod
    def _delete_old_data():
        date_to = utils.dates_helper.days_before(utils.dates_helper.local_today(), CELERY_RESULTS_DATA_KEEP_DAYS)

        django_celery_results.models.TaskResult.objects.filter(date_created__lte=date_to).delete()
