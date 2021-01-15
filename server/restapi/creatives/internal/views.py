import rest_framework.permissions
import rest_framework.response
from django.db import transaction
from django.db.models import Q

import core.features.creatives
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class CanUseCreativeView(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_see_creative_library"))


class CreativeViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated, CanUseCreativeView)
    serializer = serializers.CreativeSerializer

    def get(self, request, creative_id):
        creative = zemauth.access.get_creative(request.user, Permission.READ, creative_id)
        return self.response_ok(self.serializer(creative, context={"request": request}).data)

    def list(self, request):
        qpe = serializers.CreativeQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            creatives_qs = (
                core.features.creatives.Creative.objects.filter_by_account(account)
                .select_related("agency", "account")
                .order_by("-created_dt")
            )
        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            creatives_qs = (
                core.features.creatives.Creative.objects.filter_by_agency_and_related_accounts(agency)
                .select_related("agency", "account")
                .order_by("-created_dt")
            )
        else:
            raise utils.exc.ValidationError(
                errors={"non_field_errors": "Either agency id or account id must be provided."}
            )

        keyword = qpe.validated_data.get("keyword")
        if keyword is not None:
            creatives_qs = self._filter_by_keyword(creatives_qs, keyword)

        creative_type = qpe.validated_data.get("creative_type")
        if creative_type is not None:
            creatives_qs = self._filter_by_creative_type(creatives_qs, creative_type)

        tags = qpe.validated_data.get("tags")
        if tags is not None:
            creatives_qs = self._filter_by_tags(creatives_qs, tags)

        paginator = StandardPagination()
        creatives_qs_paginated = paginator.paginate_queryset(creatives_qs, request)
        return paginator.get_paginated_response(
            self.serializer(creatives_qs_paginated, many=True, context={"request": request}).data
        )

    @staticmethod
    def _filter_by_keyword(queryset, value):
        return queryset.filter(Q(url__icontains=value) | Q(title__icontains=value) | Q(description__icontains=value))

    @staticmethod
    def _filter_by_creative_type(queryset, value):
        return queryset.filter(type=value)

    @staticmethod
    def _filter_by_tags(queryset, value):
        return queryset.filter(tags__name__in=value)


class CreativeBatchViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated, CanUseCreativeView)
    serializer = serializers.CreativeBatchSerializer

    def validate(self, request):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def create(self, request):
        serializer = self.serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        agency_id = data.get("agency_id")
        data["agency"] = (
            zemauth.access.get_agency(request.user, Permission.WRITE, agency_id) if agency_id is not None else None
        )

        account_id = data.get("account_id")
        data["account"] = (
            zemauth.access.get_account(request.user, Permission.WRITE, account_id) if account_id is not None else None
        )

        with transaction.atomic():
            batch = core.features.creatives.CreativeBatch.objects.create(
                request, data.get("name"), agency=data.get("agency"), account=data.get("account")
            )
            batch.update(request, **data)
            batch.set_creative_tags(request, data.get("tags"))

        return self.response_ok(self.serializer(batch, context={"request": request}).data, status=201)

    def put(self, request, batch_id):
        serializer = self.serializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        batch = zemauth.access.get_creative_batch(request.user, Permission.WRITE, batch_id)
        batch.update(request, **data)

        tags = data.get("tags")
        if tags:
            batch.set_creative_tags(request, tags)

        return self.response_ok(self.serializer(batch, context={"request": request}).data)