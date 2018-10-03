from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.common.permissions import CanEditPublisherGroupsPermission
import restapi.access

import rest_framework.viewsets

import core.features.publisher_groups
import utils.exc

from . import serializers


class PublisherGroupViewSet(RESTAPIBaseViewSet, rest_framework.viewsets.ModelViewSet):
    serializer_class = serializers.PublisherGroupSerializer
    lookup_url_kwarg = "publisher_group_id"
    permission_classes = RESTAPIBaseViewSet.permission_classes + (CanEditPublisherGroupsPermission,)

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
        publisher_group = self.get_object()
        if not publisher_group.can_delete():
            raise utils.exc.ValidationError("This publisher group can not be deleted")

        return super(PublisherGroupViewSet, self).destroy(request, *args, **kwargs)
