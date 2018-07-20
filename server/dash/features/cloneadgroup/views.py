from rest_framework import permissions

import automation.campaignstop
from restapi.common.views_base import RESTAPIBaseView
import restapi.access
import dash.views.navigation_helpers

from . import serializers
from . import service


class CloneAdGroup(RESTAPIBaseView):
    permission_classes = (
        permissions.IsAuthenticated,
        restapi.access.gen_permission_class("zemauth.can_clone_adgroups"),
    )

    def post(self, request):
        user = request.user
        form = serializers.CloneAdGroupSerializer(data=request.data, context=self.get_serializer_context())
        form.is_valid(raise_exception=True)

        ad_group = service.clone(
            request,
            restapi.access.get_ad_group(user, form.validated_data["ad_group_id"]),
            restapi.access.get_campaign(user, form.validated_data["destination_campaign_id"]),
            form.validated_data["destination_ad_group_name"],
            form.validated_data["clone_ads"],
        )

        response = dash.views.navigation_helpers.get_ad_group_dict(
            request.user,
            ad_group.__dict__,
            ad_group.get_current_settings(),
            ad_group.campaign.get_current_settings(),
            automation.campaignstop.get_campaignstop_state(ad_group.campaign),
            real_time_campaign_stop=ad_group.campaign.real_time_campaign_stop,
        )

        response["campaign_id"] = ad_group.campaign_id
        return self.response_ok(serializers.AdGroupSerializer(response).data)
