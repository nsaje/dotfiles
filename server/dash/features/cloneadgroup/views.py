from rest_framework import permissions
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from djangorestframework_camel_case.parser import CamelCaseJSONParser

from restapi.views import RESTAPIBaseView
import restapi.access
import dash.views.navigation_helpers

import serializers
import service


class CloneAdGroup(RESTAPIBaseView):
    permission_classes = (permissions.IsAuthenticated,
                          restapi.access.gen_permission_class('zemauth.can_clone_adgroups'))

    renderer_classes = (CamelCaseJSONRenderer,)
    parser_classes = (CamelCaseJSONParser,)

    def post(self, request):
        user = request.user
        form = serializers.CloneAdGroupSerializer(data=request.data, context=self.get_serializer_context())
        form.is_valid(raise_exception=True)

        ad_group = service.clone(request,
                                 restapi.access.get_ad_group(user, form.validated_data['ad_group_id']),
                                 restapi.access.get_campaign(
                                     user, form.validated_data['destination_campaign_id']),
                                 form.validated_data['destination_ad_group_name'])

        response = dash.views.navigation_helpers.get_ad_group_dict(
            request.user, ad_group, ad_group.get_current_settings(), ad_group.campaign.get_current_settings())
        return self.response_ok(serializers.AdGroupSerializer(response).data)
