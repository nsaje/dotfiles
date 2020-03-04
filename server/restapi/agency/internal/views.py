import rest_framework.permissions

import core.models
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class AgencyViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.AgencySerializer

    def list(self, request):
        accounts = core.models.Account.objects.filter_by_user(request.user)
        agencies = core.models.Agency.objects.filter_by_user(request.user).union(
            core.models.Agency.objects.filter(account__in=accounts)
        )
        return self.response_ok(self.serializer(agencies, many=True, context={"request": request}).data)
