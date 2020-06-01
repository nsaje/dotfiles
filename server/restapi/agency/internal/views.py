import rest_framework.permissions

import core.models
import zemauth.features.entity_permission.helpers
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class AgencyViewSet(RESTAPIBaseViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.AgencySerializer

    def list(self, request):
        accounts_user_perm = core.models.Account.objects.filter_by_user(request.user)
        accounts_entity_perm = core.models.Account.objects.filter_by_entity_permission(request.user, Permission.READ)

        agencies_user_perm = core.models.Agency.objects.filter_by_user(request.user)
        agencies_user_perm |= core.models.Agency.objects.filter(account__in=accounts_user_perm).distinct()

        agencies_entity_perm = core.models.Agency.objects.filter_by_entity_permission(request.user, Permission.READ)
        agencies_entity_perm |= core.models.Agency.objects.filter(account__in=accounts_entity_perm).distinct()

        agencies = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            request.user, Permission.READ, agencies_user_perm, agencies_entity_perm
        )

        return self.response_ok(self.serializer(agencies, many=True, context={"request": request}).data)
