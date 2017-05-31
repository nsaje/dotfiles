from rest_framework import permissions
from djangorestframework_camel_case.render import CamelCaseJSONRenderer

import restapi.views

import service
import serializers


class TaxonomyTreeView(restapi.views.RESTAPIBaseView):
    renderer_classes = (CamelCaseJSONRenderer,)
    permission_classes = (
        permissions.IsAuthenticated,
        restapi.access.gen_permission_class('can_use_bluekai_targeting')
    )

    def get(self, request, *args, **kwargs):
        tree = service.get_tree()
        return self.response_ok(serializers.BlueKaiCategorySerializer(tree).data)
