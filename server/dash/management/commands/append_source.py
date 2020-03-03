import core.models
import utils.exc
from core.features.source_adoption import append_source
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = "Add additional source (additional_source_id) to ad groups targeting another source (base_source_id) and have source autoadding enabled"

    def add_arguments(self, parser):
        parser.add_argument("base_source_id", type=int)
        parser.add_argument("additional_source_id", type=int)
        parser.add_argument("--append-everywhere", dest="append_everywhere", action="store_true")

    def handle(self, *args, **options):
        try:
            base_source = core.models.Source.objects.get(id=int(options.get("base_source_id")))
            additional_source = core.models.Source.objects.get(id=int(options.get("additional_source_id")))

        except core.models.Source.DoesNotExist:
            raise utils.exc.MissingDataError("Source does not exist")

        append_source(base_source, additional_source, append_to_all_accounts=options.get("append_everywhere", False))
