from django.conf import settings

from etl import daily_statements
from utils import dates_helper
from utils import metrics_compat
from utils.command_helpers import Z1Command


class Command(Z1Command):
    @metrics_compat.timer("etl.oen_daily_statements")
    def handle(self, *args, **options):
        yesterday = dates_helper.local_yesterday()
        daily_statements.reprocess_daily_statements(
            yesterday, account_id=settings.HARDCODED_ACCOUNT_ID_OEN, exclude_oen=False
        )
