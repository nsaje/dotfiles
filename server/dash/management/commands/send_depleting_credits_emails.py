import core.features.credit_notifications
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    def handle(self, *args, **options):
        core.features.credit_notifications.check_and_notify_depleting_credits()
