from rest_framework import permissions

import dash.features.bluekai
import restapi.common.views_base

from . import serializers


class CanUseBluekaiTargetingPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_use_bluekai_targeting"))


class TaxonomyTreeViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated, CanUseBluekaiTargetingPermission)

    def get(self, request, *args, **kwargs):
        tree = dash.features.bluekai.service.get_tree()
        return self.response_ok(serializers.BlueKaiCategorySerializer(tree).data)
