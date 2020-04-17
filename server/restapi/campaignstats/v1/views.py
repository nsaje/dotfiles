import redshiftapi.api_quickstats
import restapi.access
import utils.exc
from restapi.campaignstats.v1 import serializers
from restapi.common.views_base import RESTAPIBaseViewSet


class CampaignStatsViewSet(RESTAPIBaseViewSet):
    def get(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id)
        from_date = self.request.query_params.get("from", None)
        to_date = self.request.query_params.get("to", None)
        if not from_date or not to_date:
            raise utils.exc.ValidationError("Missing from or to parameter")
        stats = redshiftapi.api_quickstats.query_campaign(campaign.id, from_date, to_date)
        return self.response_ok(serializers.CampaignStatsSerializer(stats).data)
