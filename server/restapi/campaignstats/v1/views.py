import redshiftapi.api_quickstats
import restapi.access
from restapi.campaignstats.v1 import serializers
from restapi.common.views_base import RESTAPIBaseViewSet


class CampaignStatsViewSet(RESTAPIBaseViewSet):
    def get(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        qpe = serializers.CampaignStatsQueryParams(data=request.query_params)
        qpe.is_valid(raise_exception=True)
        from_date = qpe.validated_data.get("from_")
        to_date = qpe.validated_data.get("to")
        stats = redshiftapi.api_quickstats.query_campaign(campaign.id, from_date, to_date)
        return self.response_ok(serializers.CampaignStatsSerializer(stats).data)
