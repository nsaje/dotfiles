from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

import dash.constants
import dash.models
from utils import db_router
from utils import zlogging

from .base import K1APIView

logger = zlogging.getLogger(__name__)


class R1PixelMappingView(K1APIView):
    @db_router.use_read_replica()
    @method_decorator(cache_page(10 * 60, cache="dash_db_cache"))
    def get(self, request, account_id):
        conversion_pixels = dash.models.ConversionPixel.objects.filter(account_id=account_id).filter(archived=False)
        data = [conversion_pixel.slug for conversion_pixel in conversion_pixels]
        return self.response_ok(data)


class R1AdGroupMappingView(K1APIView):
    @db_router.use_read_replica()
    @method_decorator(cache_page(10 * 60, cache="dash_db_cache"))
    def get(self, request, account_id):
        limit = int(request.GET.get("limit", 1000000))
        marker = request.GET.get("marker")

        ad_groups = (
            dash.models.AdGroup.objects.all()
            .exclude_archived()
            .select_related("campaign")
            .filter(campaign__account_id=account_id)
            .only("id", "campaign_id", "campaign__account_id")
        )

        if marker:
            ad_groups = ad_groups.filter(pk__gt=int(marker))
        ad_groups = ad_groups.order_by("pk")[:limit]

        data = [{"ad_group_id": ag.id, "campaign_id": ag.campaign_id} for ag in ad_groups]

        return self.response_ok(data)
