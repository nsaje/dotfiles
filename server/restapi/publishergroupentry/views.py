from restapi.common.views_base import RESTAPIBaseViewSet
from restapi.common.pagination import StandardPagination
from restapi.common.permissions import CanEditPublisherGroupsPermission
import restapi.access

from rest_framework.response import Response
import rest_framework.viewsets

import core.publisher_groups
from . import serializers


class PublisherGroupEntryViewSet(RESTAPIBaseViewSet, rest_framework.viewsets.ModelViewSet):
    pagination_class = StandardPagination
    permission_classes = RESTAPIBaseViewSet.permission_classes + (CanEditPublisherGroupsPermission,)

    lookup_url_kwarg = 'entry_id'

    def get_serializer_class(self):
        if self.request.user.has_perm('zemauth.can_access_additional_outbrain_publisher_settings'):
            return serializers.OutbrainPublisherGroupEntrySerializer
        return serializers.PublisherGroupEntrySerializer

    def get_queryset(self):
        publisher_group = core.publisher_groups.PublisherGroup.objects.get(pk=self.kwargs['publisher_group_id'])
        restapi.access.get_account(self.request.user, publisher_group.account_id)
        return publisher_group.entries.all().select_related('source')

    def create(self, request, *args, **kwargs):
        # support create multiple through the "many" parameter
        serializer = self.get_serializer(data=request.data, many=not isinstance(request.data, dict))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def perform_create(self, serializer):
        publisher_group = core.publisher_groups.PublisherGroup.objects.get(pk=self.kwargs['publisher_group_id'])
        restapi.access.get_account(self.request.user, publisher_group.account_id)
        serializer.save(publisher_group_id=self.kwargs['publisher_group_id'])
