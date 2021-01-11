import rest_framework.permissions
import rest_framework.response

from core import models
from restapi.common.pagination import StandardLimitOffsetPagination
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class SourceViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.SourceSerializer

    def list(self, request):
        sources = models.Source.objects.filter(deprecated=False, released=True)
        paginator = StandardLimitOffsetPagination()
        sources_paginated = paginator.paginate_queryset(sources, request)

        return paginator.get_paginated_response(
            self.serializer(sources_paginated, many=True, context={"request": request}).data
        )
