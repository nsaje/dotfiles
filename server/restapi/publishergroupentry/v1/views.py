import rest_framework.viewsets
from rest_framework.response import Response

import core.features.publisher_groups
import zemauth.access
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.publishergroupentry.v1 import serializers
from zemauth.features.entity_permission import Permission


class PublisherGroupEntryViewSet(RESTAPIBaseViewSet, rest_framework.viewsets.ModelViewSet):
    pagination_class = StandardPagination
    permission_classes = RESTAPIBaseViewSet.permission_classes

    lookup_url_kwarg = "entry_id"

    def get_serializer_class(self):
        if self.request.user.has_perm("zemauth.can_access_additional_outbrain_publisher_settings"):
            return serializers.OutbrainPublisherGroupEntrySerializer
        return serializers.PublisherGroupEntrySerializer

    def get_queryset(self):
        publisher_group = core.features.publisher_groups.PublisherGroup.objects.get(
            pk=self.kwargs["publisher_group_id"]
        )
        if publisher_group.account_id is not None:
            zemauth.access.get_account(self.request.user, Permission.READ, publisher_group.account_id)
        else:
            zemauth.access.get_agency(self.request.user, Permission.READ, publisher_group.agency_id)
        return publisher_group.entries.all().select_related("source")

    def create(self, request, *args, **kwargs):
        # support create multiple through the "many" parameter
        serializer = self.get_serializer(data=request.data, many=not isinstance(request.data, dict))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def perform_create(self, serializer):
        publisher_group = core.features.publisher_groups.PublisherGroup.objects.get(
            pk=self.kwargs["publisher_group_id"]
        )
        if publisher_group.account_id is not None:
            zemauth.access.get_account(self.request.user, Permission.WRITE, publisher_group.account_id)
        else:
            zemauth.access.get_agency(self.request.user, Permission.WRITE, publisher_group.agency_id)
        serializer.save(publisher_group_id=self.kwargs["publisher_group_id"])

    def update(self, request, *args, **kwargs):
        zemauth.access.get_publisher_group(request.user, Permission.WRITE, kwargs["publisher_group_id"])
        return super().update(request, args, kwargs)

    def destroy(self, request, *args, **kwargs):
        zemauth.access.get_publisher_group(request.user, Permission.WRITE, kwargs["publisher_group_id"])
        return super().destroy(request, args, kwargs)
