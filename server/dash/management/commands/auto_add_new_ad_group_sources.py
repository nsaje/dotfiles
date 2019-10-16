import core.models
import structlog
import utils.exc
from core.features.source_adoption import auto_add_new_ad_group_sources
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):
    help = "Add source to ad groups of accounts which have automatic addition of newly released sources turned on."

    def add_arguments(self, parser):
        parser.add_argument("source_id", type=int)

    def handle(self, *args, **options):
        try:
            source = core.models.Source.objects.get(id=int(options.get("source_id")))

        except core.models.Source.DoesNotExist:
            raise utils.exc.MissingDataError("Source does not exist")

        auto_add_new_ad_group_sources(source)
