from rest_framework import permissions

import dash.features.bluekai
import restapi.bluekai.v1.views
import restapi.common.views_base
import restapi.serializers.targeting

from . import serializers


class TaxonomyTreeInternalViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        tree = dash.features.bluekai.service.get_tree()
        return self.response_ok(serializers.BlueKaiCategoryInternalSerializer(tree).data)


class SegmentReachViewSet(restapi.common.views_base.RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = restapi.serializers.targeting.AudienceSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return self.response_ok({"errors": [str(e)]})

        reach = dash.features.bluekai.service.get_reach(serializer.validated_data)
        return self.response_ok(serializers.BlueKaiReachSerializer(reach).data)
