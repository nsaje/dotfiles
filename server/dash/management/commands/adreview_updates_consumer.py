import core.features.ad_review
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):

    help = "Run adreview Kafka consumer"

    def handle(self, *args, **options):
        core.features.ad_review.start_consumer()
