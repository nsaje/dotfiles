from django.db.models import Q

import core.features.bid_modifiers
import core.models
import dash.constants
from utils import db_router

from .base import K1APIView


class BidModifiersView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        limit = int(request.GET.get("limit", 500))
        marker = request.GET.get("marker")
        ad_group_ids = request.GET.get("ad_group_ids")
        type_ = request.GET.get("type")

        qs = core.features.bid_modifiers.BidModifier.objects.all().order_by("pk")

        # TODO: RTAP: remove after migration
        force_source_bm_ad_group_ids = core.models.AdGroup.objects.filter(
            Q(campaign__account__agency__isnull=False)
            & Q(campaign__account__agency__uses_realtime_autopilot=True)
            & (
                Q(campaign__settings__autopilot=True)
                | ~Q(settings__autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE)
            )
        ).values_list("id", flat=True)

        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(",")
            qs = qs.filter(ad_group_id__in=ad_group_ids)
            force_source_bm_ad_group_ids = force_source_bm_ad_group_ids.filter(id__in=ad_group_ids)

        if type_:
            qs = qs.filter(type=type_)
        if marker:
            qs = qs.filter(pk__gt=int(marker))
        qs = qs[:limit]

        force_source_bm_ad_group_ids = set(force_source_bm_ad_group_ids)

        return self.response_ok(
            [
                {
                    "id": item.id,
                    "ad_group_id": item.ad_group_id,
                    "target": item.target,
                    "type": item.type,
                    "source": item.source_slug,
                    "modifier": 1.0
                    if item.type == core.features.bid_modifiers.constants.BidModifierType.SOURCE
                    and item.ad_group_id in force_source_bm_ad_group_ids
                    else item.modifier,
                }
                for item in qs
            ]
        )
