import dash.models
from utils import db_router
from utils import zlogging

from .base import K1APIView

logger = zlogging.getLogger(__name__)


class SourcesView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        source_slugs = request.GET.get("source_slugs")
        sources = dash.models.Source.objects.all().select_related(
            "defaultsourcesettings", "defaultsourcesettings__credentials", "source_type"
        )
        if source_slugs:
            sources = sources.filter(bidder_slug__in=source_slugs.split(","))

        response = []
        for source in sources:
            source_dict = {
                "id": source.id,
                "name": source.name,
                "slug": source.tracking_slug,
                "credentials": None,
                "source_type": source.source_type.type,
                "bidder_slug": source.bidder_slug,
                "supports_retargeting": source.supports_retargeting,
            }
            try:
                default_credentials = source.defaultsourcesettings.credentials
                if default_credentials:
                    source_dict["credentials"] = {
                        "id": default_credentials.id,
                        "credentials": default_credentials.credentials,
                    }
            except dash.models.DefaultSourceSettings.DoesNotExist:
                pass
            response.append(source_dict)
        return self.response_ok(response)
