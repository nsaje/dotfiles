import core.models
import restapi.access
import restapi.adgroup.v1.views

from . import helpers
from . import serializers


class AdGroupViewSet(restapi.adgroup.v1.views.AdGroupViewSet):
    def validate(self, request):
        serializer = serializers.AdGroupSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return self.response_ok(None)

    def defaults(self, request):
        campaign_id = request.query_params.get("campaignId", None)
        if not campaign_id:
            raise serializers.ValidationError("Must pass campaignId parameter")
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        ad_group = core.models.AdGroup.objects.get_restapi_default(request, campaign)
        extra_data = helpers.get_extra_data(request.user, ad_group)
        return self.response_ok(
            data=serializers.AdGroupSerializer(ad_group.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )

    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        extra_data = helpers.get_extra_data(request.user, ad_group)
        return self.response_ok(
            data=serializers.AdGroupSerializer(ad_group.settings, context={"request": request}).data,
            extra=serializers.ExtraDataSerializer(extra_data, context={"request": request}).data,
        )
