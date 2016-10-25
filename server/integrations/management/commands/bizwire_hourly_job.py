import logging

from integrations.bizwire.internal import actions
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        actions.check_midnight_and_stop_ads()
