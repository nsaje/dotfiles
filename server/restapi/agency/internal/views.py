import rest_framework.permissions

import core.models
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class AgencyViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.AgencySerializer

    def list(self, request):
        accounts = core.models.Account.objects.filter_by_entity_permission(request.user, Permission.READ)

        agencies = core.models.Agency.objects.filter_by_entity_permission(request.user, Permission.READ).distinct()
        agencies |= core.models.Agency.objects.filter(account__in=accounts).distinct()

        return self.response_ok(self.serializer(agencies, many=True, context={"request": request}).data)
