import logging

from integrations.bizwire.internal import actions
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        actions.check_midnight_and_stop_ads()
        actions.check_time_and_create_new_ad_groups()
        actions.check_date_and_stop_old_ad_groups()
