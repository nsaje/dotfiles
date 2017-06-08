from rest_framework import permissions
from djangorestframework_camel_case.render import CamelCaseJSONRenderer

import restapi.views
from restapi.serializers.targeting import DemographicSerializer

import service
import serializers


class TaxonomyTreeView(restapi.views.RESTAPIBaseView):
    renderer_classes = (CamelCaseJSONRenderer,)
    permission_classes = (
        permissions.IsAuthenticated,
        restapi.access.gen_permission_class('zemauth.can_use_bluekai_targeting')
    )

    def get(self, request, *args, **kwargs):
        tree = service.get_tree()
        return self.response_ok(serializers.BlueKaiCategorySerializer(tree).data)


class SegmentReachView(restapi.views.RESTAPIBaseView):
    renderer_classes = (CamelCaseJSONRenderer,)
    permission_classes = (
        permissions.IsAuthenticated,
        restapi.access.gen_permission_class('zemauth.can_use_bluekai_targeting')
    )

    def post(self, request, *args, **kwargs):
        serializer = DemographicSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return self.response_ok({'errors': [e.message]})

        reach = service.get_reach(serializer.validated_data)
        return self.response_ok(serializers.BlueKaiReachSerializer(reach).data)
