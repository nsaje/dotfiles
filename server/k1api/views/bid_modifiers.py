import core.features.bid_modifiers

from .base import K1APIView


class BidModifiersView(K1APIView):
    def get(self, request):
        limit = int(request.GET.get("limit", 500))
        marker = request.GET.get("marker")
        ad_group_ids = request.GET.get("ad_group_ids")
        type_ = request.GET.get("type")

        qs = core.features.bid_modifiers.BidModifier.objects.all().order_by("pk")
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(",")
            qs = qs.filter(ad_group_id__in=ad_group_ids)
        if type_:
            qs = qs.filter(type=type_)
        if marker:
            qs = qs.filter(pk__gt=int(marker))
        qs = qs[:limit]

        return self.response_ok(
            [
                {
                    "id": item.id,
                    "ad_group_id": item.ad_group_id,
                    "target": item.target,
                    "type": item.type,
                    "source": item.source_slug,
                    "modifier": item.modifier,
                }
                for item in qs
            ]
        )
