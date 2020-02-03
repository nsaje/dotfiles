import rest_framework.permissions
import rest_framework.response

import restapi.access
import restapi.common.helpers
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class SourceViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.SourceSerializer

    def list(self, request, agency_id):
        agency = restapi.access.get_agency(request.user, agency_id)
        sources = restapi.common.helpers.get_available_sources(request.user, agency)
        return self.response_ok(self.serializer(sources, many=True, context={"request": request}).data)
