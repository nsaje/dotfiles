import rest_framework.permissions

import core.models
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class AgencyViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.AgencySerializer

    def list(self, request):
        agencies = core.models.Agency.objects.all().filter_by_user(request.user)
        return self.response_ok(self.serializer(agencies, many=True, context={"request": request}).data)
