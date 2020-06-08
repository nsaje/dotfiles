import rest_framework.permissions
import rest_framework.response
from django.db import transaction
from django.db.models import Q

import core.features.deals
import core.models
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class DirectDealViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.DirectDealSerializer

    def validate(self, request):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def get(self, request, deal_id):
        deal = zemauth.access.get_direct_deal(request.user, Permission.READ, deal_id)
        return self.response_ok(self.serializer(deal, context={"request": request}).data)

    def list(self, request):
        qpe = serializers.DirectDealQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")
        agency_only = qpe.validated_data.get("agency_only", None)

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            deal_items = (
                core.features.deals.DirectDeal.objects.filter_by_account(account)
                .select_related("source", "account")
                .order_by("-created_dt")
            )
        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            if agency_only is not None and agency_only:
                deal_items = (
                    core.features.deals.DirectDeal.objects.filter_by_agency(agency)
                    .select_related("source", "agency")
                    .order_by("-created_dt")
                )
            else:
                deal_items = (
                    core.features.deals.DirectDeal.objects.filter(Q(agency=agency) | Q(account__agency=agency))
                    .select_related("source", "agency")
                    .order_by("-created_dt")
                )

        else:
            raise utils.exc.ValidationError(
                errors={"non_field_errors": "Either agency id or account id must be provided."}
            )

        keyword = qpe.validated_data.get("keyword")
        if keyword:
            deal_items = deal_items.filter(
                Q(name__icontains=keyword)
                | Q(deal_id__icontains=keyword)
                | Q(source__name__icontains=keyword)
                | Q(source__bidder_slug__icontains=keyword)
            )

        if not request.user.has_perm("zemauth.can_see_internal_deals"):
            deal_items = deal_items.exclude(is_internal=True)

        paginator = StandardPagination()
        deal_items_paginated = paginator.paginate_queryset(deal_items, request)
        return paginator.get_paginated_response(
            self.serializer(deal_items_paginated, many=True, context={"request": request}).data
        )

    def put(self, request, deal_id):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        deal = zemauth.access.get_direct_deal(request.user, Permission.WRITE, deal_id)
        deal.update(request, **data)
        return self.response_ok(self.serializer(deal, context={"request": request}).data)

    def remove(self, request, deal_id):
        deal = zemauth.access.get_direct_deal(request.user, Permission.WRITE, deal_id)
        deal.delete()
        return rest_framework.response.Response(None, status=204)

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            new_deal = core.features.deals.DirectDeal.objects.create(
                request,
                agency=data.get("agency"),
                account=data.get("account"),
                source=data.get("source"),
                deal_id=data.get("deal_id"),
                name=data.get("name"),
            )
            new_deal.update(request, **data)

        return self.response_ok(self.serializer(new_deal, context={"request": request}).data, status=201)

    def list_connections(self, request, deal_id):
        deal = zemauth.access.get_direct_deal(request.user, Permission.READ, deal_id)
        deal_connection_items = (
            core.features.deals.DirectDealConnection.objects.filter_by_deal(deal)
            .select_related(
                "account", "account__settings", "campaign", "campaign__settings", "adgroup", "adgroup__settings"
            )
            .order_by("-created_dt")
        )
        return self.response_ok(
            serializers.DirectDealConnectionSerializer(
                deal_connection_items, many=True, context={"request": request}
            ).data
        )

    def remove_connection(self, request, deal_id, deal_connection_id):
        deal = zemauth.access.get_direct_deal(request.user, Permission.WRITE, deal_id)
        deal_connection = zemauth.access.get_direct_deal_connection(deal_connection_id, deal)
        deal_connection.delete()
        return rest_framework.response.Response(None, status=204)
