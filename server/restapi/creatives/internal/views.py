import rest_framework.permissions
import rest_framework.response
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
