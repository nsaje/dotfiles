import core.models
from core.features.source_adoption import deprecate_sources
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = "Deprecate sources"

    def add_arguments(self, parser):
        parser.add_argument("source_ids", type=str, nargs="+", help="Source IDs")

    def handle(self, *args, **options):
        source_ids = set(int(s) for s in options["source_ids"] if s.isdigit())
        if not source_ids:
            return
        sources = core.models.Source.objects.filter(deprecated=False, pk__in=source_ids)
        deprecate_sources(sources)
