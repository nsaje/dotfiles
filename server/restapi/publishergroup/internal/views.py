import rest_framework.response
from django.db.models import Q
from rest_framework import permissions

import core.features.publisher_groups
import restapi.access
import utils.exc
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class PublisherGroupViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        query_params = serializers.PublisherGroupQueryParamsExpectations(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        agency_id = query_params.validated_data.get("agency_id")
        account_id = query_params.validated_data.get("account_id")

        publisher_groups_items = core.features.publisher_groups.PublisherGroup.objects.order_by("-created_dt", "name")

        if account_id is not None:
            account = restapi.access.get_account(request.user, account_id)
            publisher_groups_items = publisher_groups_items.filter_by_account(account)

        elif agency_id is not None:
            agency = restapi.access.get_agency(request.user, agency_id)
            publisher_groups_items = publisher_groups_items.filter(Q(agency=agency) | Q(account__agency=agency))

        else:
            raise utils.exc.ValidationError("Either agency id or account id must be provided.")

        if not query_params.validated_data["include_implicit"]:
            publisher_groups_items = publisher_groups_items.filter_explicit()

        keyword = query_params.validated_data.get("keyword")
        if keyword is not None:
            publisher_groups_items = publisher_groups_items.search(search_expression=keyword)

        paginator = StandardPagination()
        paginated_publisher_groups = paginator.paginate_queryset(publisher_groups_items, request)
        return paginator.get_paginated_response(
            serializers.PublisherGroupSerializer(paginated_publisher_groups, many=True).data
        )

    def remove(self, request, publisher_group_id):
        publisher_group = restapi.access.get_publisher_group(request.user, publisher_group_id)
        publisher_group.delete()
        return rest_framework.response.Response(None, status=204)
