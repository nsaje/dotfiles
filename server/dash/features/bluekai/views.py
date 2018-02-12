from rest_framework import permissions

import restapi.views
from restapi.serializers.targeting import AudienceSerializer

from . import service
from . import serializers


class TaxonomyTreeInternalView(restapi.views.RESTAPIBaseView):
    permission_classes = (
        permissions.IsAuthenticated,
        restapi.access.gen_permission_class('zemauth.can_use_bluekai_targeting')
    )

    def get(self, request, *args, **kwargs):
        tree = service.get_tree()
        return self.response_ok(serializers.BlueKaiCategoryInternalSerializer(tree).data)


class TaxonomyTreeView(restapi.views.RESTAPIBaseView):
    permission_classes = (
        permissions.IsAuthenticated,
        restapi.access.gen_permission_class('zemauth.can_use_bluekai_targeting')
    )

    def get(self, request, *args, **kwargs):
        tree = service.get_tree()
        return self.response_ok(serializers.BlueKaiCategorySerializer(tree).data)


class SegmentReachView(restapi.views.RESTAPIBaseView):
    permission_classes = (
        permissions.IsAuthenticated,
        restapi.access.gen_permission_class('zemauth.can_use_bluekai_targeting')
    )

    def post(self, request, *args, **kwargs):
        serializer = AudienceSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return self.response_ok({'errors': [str(e)]})

        reach = service.get_reach(serializer.validated_data)
        return self.response_ok(serializers.BlueKaiReachSerializer(reach).data)
