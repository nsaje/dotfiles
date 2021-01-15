import rest_framework.permissions

import core.models.tags.creative
import utils.exc
import zemauth.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class CanUseCreativeTagView(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_see_creative_library"))


class CreativeTagViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated, CanUseCreativeTagView)

    def list(self, request):
        qpe = serializers.CreativeTagQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)

        agency_id = qpe.validated_data.get("agency_id")
        account_id = qpe.validated_data.get("account_id")

        if account_id is not None:
            account = zemauth.access.get_account(request.user, Permission.READ, account_id)
            tags_qs = core.models.tags.creative.CreativeTag.objects.filter_by_account(account)
        elif agency_id is not None:
            agency = zemauth.access.get_agency(request.user, Permission.READ, agency_id)
            tags_qs = core.models.tags.creative.CreativeTag.objects.filter_by_agency_and_related_accounts(agency)
        else:
            raise utils.exc.ValidationError(
                errors={"non_field_errors": "Either agency id or account id must be provided."}
            )

        keyword = qpe.validated_data.get("keyword")
        if keyword is not None:
            tags_qs = self._filter_by_keyword(tags_qs, keyword)

        tags_qs = tags_qs.values_list("name", flat=True)

        paginator = StandardPagination()
        tags_qs_paginated = paginator.paginate_queryset(tags_qs, request)
        return paginator.get_paginated_response(tags_qs_paginated)

    @staticmethod
    def _filter_by_keyword(queryset, value):
        return queryset.filter(name__icontains=value)
