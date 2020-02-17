from rest_framework import permissions

import core.features.publisher_groups
import restapi.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class PublisherGroupSearchViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, agency_id):
        qpe = serializers.PublisherGroupQueryParamsExpectations(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        agency = restapi.access.get_agency(request.user, agency_id)
        paginator = StandardPagination()
        queryset = (
            core.features.publisher_groups.PublisherGroup.objects.search(
                search_expression=qpe.validated_data.get("keyword", "")
            )
            .filter(agency=agency, account__isnull=True)
            .order_by("name")
        )
        paginated_publisher_groups = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(
            serializers.PublisherGroupSerializer(paginated_publisher_groups, many=True).data
        )
