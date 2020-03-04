import rest_framework.permissions
import rest_framework.response

import core.models
import restapi.common.helpers
import utils.exc
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class SourceViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.SourceSerializer

    def list(self, request, agency_id):
        agency = core.models.Agency.objects.filter(id=int(agency_id)).first()
        if not agency:
            raise utils.exc.MissingDataError("Agency does not exist")

        sources = restapi.common.helpers.get_available_sources(request.user, agency)
        return self.response_ok(self.serializer(sources, many=True, context={"request": request}).data)
