from django.conf import settings
from django.db.models import Q

import core.features.bid_modifiers
import core.features.source_groups
import core.models
from utils import db_router

from .base import K1APIView


class BidModifiersView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        limit = int(request.GET.get("limit", 500))
        marker = request.GET.get("marker")
        ad_group_ids = request.GET.get("ad_group_ids")
        type_ = request.GET.get("type")

        source_groups_id_slugs_mapping = core.features.source_groups.get_source_id_slugs_mapping()

        qs = core.features.bid_modifiers.BidModifier.objects.exclude(
            (
                Q(type=core.features.bid_modifiers.constants.BidModifierType.SOURCE)
                & Q(target__in=[str(sid) for sid in source_groups_id_slugs_mapping.keys()])
                | Q(type=core.features.bid_modifiers.constants.BidModifierType.PUBLISHER)
                & Q(source_id__in=source_groups_id_slugs_mapping.keys())
                | Q(type=core.features.bid_modifiers.constants.BidModifierType.PLACEMENT)
                & Q(source_id__in=source_groups_id_slugs_mapping.keys())
            ),
            ad_group__campaign__account__agency__uses_source_groups=True,
        ).order_by("pk")

        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(",")
            qs = qs.filter(ad_group_id__in=ad_group_ids)

        if type_:
            qs = qs.filter(type=type_)
        if marker:
            qs = qs.filter(pk__gt=int(marker))
        qs = qs[:limit]

        response = []
        for bid_modifier in qs:
            item = {
                "ad_group_id": bid_modifier.ad_group_id,
                "target": bid_modifier.target,
                "type": bid_modifier.type,
                "source": bid_modifier.source_slug,
                "modifier": bid_modifier.modifier,
            }

            if bid_modifier.type == core.features.bid_modifiers.constants.BidModifierType.SOURCE:
                response += self._generate_source_groups_bid_modifiers(
                    bid_modifier, item, int(bid_modifier.target), "target", str
                )

            elif bid_modifier.type in (
                core.features.bid_modifiers.constants.BidModifierType.PUBLISHER,
                core.features.bid_modifiers.constants.BidModifierType.PLACEMENT,
            ):
                response += self._generate_source_groups_bid_modifiers(
                    bid_modifier,
                    item,
                    bid_modifier.source_id,
                    "source",
                    lambda sid: source_groups_id_slugs_mapping[sid]["bidder_slug"],
                )

            else:
                response.append(item)

        return self.response_ok(response)

    def _generate_source_groups_bid_modifiers(self, bid_modifier, item, source_id, field, update_fn):
        response = []

        source_group = settings.SOURCE_GROUPS.get(source_id)
        if source_group and bid_modifier.ad_group.campaign.account.agency.uses_source_groups:
            for grouped_source_id in source_group:
                grouped_item = item.copy()
                grouped_item[field] = update_fn(grouped_source_id)
                response.append(grouped_item)

        if (
            source_id != settings.HARDCODED_SOURCE_ID_OUTBRAINRTB
            or bid_modifier.ad_group.campaign.account_id != settings.HARDCODED_ACCOUNT_ID_OEN
        ):
            response.append(item)

        return response
