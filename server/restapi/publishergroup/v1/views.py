import rest_framework.viewsets
from rest_framework import status
from rest_framework.response import Response

import core.features.publisher_groups
import restapi.access
from restapi.common import pagination
from restapi.common.permissions import CanEditPublisherGroupsPermission
from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.publishergroup.v1 import serializers


class PublisherGroupViewSet(RESTAPIBaseViewSet, rest_framework.viewsets.ModelViewSet):
    serializer_class = serializers.PublisherGroupSerializer
    lookup_url_kwarg = "publisher_group_id"
    permission_classes = RESTAPIBaseViewSet.permission_classes + (CanEditPublisherGroupsPermission,)
    pagination_class = pagination.MarkerOffsetPagination

    @property
    def paginator(self):
        paginator = super().paginator
        paginator.default_limit = 500000
        paginator.max_limit = 500000  # NOTE(nsaje): OEN could fetch ~400k pub groups before timeout
        return paginator

    def get_queryset(self):
        account = restapi.access.get_account(
            self.request.user, self.kwargs["account_id"]
        )  # check user has account access
        return core.features.publisher_groups.PublisherGroup.objects.all().filter_by_account(account)

    def perform_create(self, serializer):
        restapi.access.get_account(self.request.user, self.kwargs["account_id"])
        serializer.save(request=self.request, account_id=self.kwargs["account_id"])

    def perform_update(self, serializer):
        serializer.save(request=self.request, account_id=self.kwargs["account_id"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
