import logging

from django.db.models import F

import core.features.bid_modifiers
import dash.constants
import dash.models
from utils import db_router

from .base import K1APIView

logger = logging.getLogger(__name__)


class PublisherGroupsView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        account_id = request.GET.get("account_id")

        publisher_groups = dash.models.PublisherGroup.objects.all().filter_by_active_adgroups()
        if account_id:
            publisher_groups = publisher_groups.filter_by_account(dash.models.Account.objects.get(pk=account_id))

        return self.response_ok(list(publisher_groups.values("id", "account_id")))


class PublisherGroupsEntriesView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        account_id = request.GET.get("account_id")
        source_slug = request.GET.get("source_slug")
        publisher_group_ids = request.GET.get("publisher_group_ids")
        offset = request.GET.get("offset") or 0
        limit = request.GET.get("limit")

        if not limit:
            return self.response_error("Limit parameter is missing", status=400)
        offset = int(offset)
        limit = int(limit)

        # ensure unique order
        entries = dash.models.PublisherGroupEntry.objects.all().order_by("pk")
        if account_id:
            publisher_groups = dash.models.PublisherGroup.objects.all().filter_by_account(
                dash.models.Account.objects.get(pk=account_id)
            )
            entries = entries.filter(publisher_group__in=publisher_groups)

        if publisher_group_ids:
            publisher_group_ids = publisher_group_ids.split(",")
            entries = entries.filter(publisher_group_id__in=publisher_group_ids)

        if source_slug:
            entries = entries.filter(source__bidder_slug=source_slug)

        return self.response_ok(
            list(
                entries[offset : offset + limit]
                .annotate(source_slug=F("source__bidder_slug"), account_id=F("publisher_group__account_id"))
                .values(
                    "source_slug",
                    "publisher_group_id",
                    "include_subdomains",
                    "outbrain_publisher_id",
                    "outbrain_section_id",
                    "outbrain_amplify_publisher_id",
                    "outbrain_engage_publisher_id",
                    "publisher",
                    "account_id",
                )
            )
        )


class PublisherBidModifiersView(K1APIView):
    def get(self, request):
        limit = int(request.GET.get("limit", 500))
        marker = request.GET.get("marker")
        ad_group_ids = request.GET.get("ad_group_ids")
        source_type = request.GET.get("source_type")

        qs = (
            core.features.bid_modifiers.BidModifier.objects.all()
            .select_related("source", "source__source_type")
            .order_by("pk")
        )
        if ad_group_ids:
            ad_group_ids = ad_group_ids.split(",")
            qs = qs.filter(ad_group_id__in=ad_group_ids)
        if source_type:
            qs = qs.filter(source__source_type__type=source_type)
        if marker:
            qs = qs.filter(pk__gt=int(marker))
        qs = qs[:limit]

        return self.response_ok(
            [
                {
                    "id": item.id,
                    "ad_group_id": item.ad_group_id,
                    "publisher": item.publisher,
                    "source": item.source.bidder_slug,
                    "modifier": item.modifier,
                }
                for item in qs
            ]
        )
