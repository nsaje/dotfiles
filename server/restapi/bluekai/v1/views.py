from rest_framework import permissions

import dash.features.bluekai
import restapi.common.views_base

from . import serializers


class TaxonomyTreeViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        tree = dash.features.bluekai.service.get_tree()
        return self.response_ok(serializers.BlueKaiCategorySerializer(tree).data)
