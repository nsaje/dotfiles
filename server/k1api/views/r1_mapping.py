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


# TODO: R1MAPPING: Remove after k1 merge
class R1MappingView(K1APIView):
    @db_router.use_read_replica()
    @method_decorator(cache_page(10 * 60, cache="dash_db_cache"))
    def get(self, request):
        accounts = [int(account) for account in request.GET.getlist("account")]

        data = {account: {"slugs": [], "ad_groups": {}} for account in accounts}

        conversion_pixels = dash.models.ConversionPixel.objects.filter(account_id__in=accounts).filter(archived=False)
        for conversion_pixel in conversion_pixels:
            data[conversion_pixel.account_id]["slugs"].append(conversion_pixel.slug)

        ad_groups = (
            dash.models.AdGroup.objects.all()
            .exclude_archived()
            .select_related("campaign")
            .filter(campaign__account_id__in=accounts)
            .only("id", "campaign_id", "campaign__account_id")
        )
        for ad_group in ad_groups:
            data[ad_group.campaign.account_id]["ad_groups"][ad_group.id] = {"campaign_id": ad_group.campaign_id}

        return self.response_ok(data)
