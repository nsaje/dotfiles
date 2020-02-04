import rest_framework.permissions
import rest_framework.response
from django.db import transaction
from django.db.models import Q

import core.features.deals
import restapi.access
import utils.exc
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class DirectDealViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.DirectDealSerializer

    def validate(self, request):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def get(self, request, deal_id):
        deal = restapi.access.get_direct_deal(request.user, deal_id)
        return self.response_ok(self.serializer(deal, context={"request": request}).data)

    def list(self, request):
        agency = (
            restapi.access.get_agency(request.user, request.query_params["agencyId"])
            if request.query_params.get("agencyId")
            else None
        )
        account = (
            restapi.access.get_account(request.user, request.query_params["accountId"])
            if request.query_params.get("accountId")
            else None
        )
        if account is not None:
            deal_items = (
                core.features.deals.DirectDeal.objects.filter_by_account(account)
                .select_related("source", "account")
                .order_by("-created_dt")
            )
        elif agency is not None:
            deal_items = (
                core.features.deals.DirectDeal.objects.filter(Q(agency=agency) | Q(account__agency=agency))
                .select_related("source", "agency")
                .order_by("-created_dt")
            )
        else:
            raise utils.exc.ValidationError(
                errors={"non_field_errors": "Either agency id or account id must be provided."}
            )

        keyword = request.query_params.get("keyword")
        if keyword:
            deal_items = deal_items.filter(
                Q(name__icontains=keyword)
                | Q(deal_id__icontains=keyword)
                | Q(source__name__icontains=keyword)
                | Q(source__bidder_slug__icontains=keyword)
            )
        paginator = StandardPagination()
        deal_items_paginated = paginator.paginate_queryset(deal_items, request)
        return paginator.get_paginated_response(
            self.serializer(deal_items_paginated, many=True, context={"request": request}).data
        )

    def put(self, request, deal_id):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        deal = restapi.access.get_direct_deal(request.user, deal_id)
        deal.update(request, **data)
        return self.response_ok(self.serializer(deal, context={"request": request}).data)

    def remove(self, request, deal_id):
        deal = restapi.access.get_direct_deal(request.user, deal_id)
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
        deal = restapi.access.get_direct_deal(request.user, deal_id)
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
        deal = restapi.access.get_direct_deal(request.user, deal_id)
        deal_connection = restapi.access.get_direct_deal_connection(request.user, deal_connection_id, deal=deal)
        deal_connection.delete()
        return rest_framework.response.Response(None, status=204)
