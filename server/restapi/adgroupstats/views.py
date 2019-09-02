import dash.features.realtimestats
import restapi.access
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class AdGroupRealtimeStatsViewSet(RESTAPIBaseViewSet):
    """ Outbrain only """

    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        stats = dash.features.realtimestats.get_ad_group_stats(ad_group)
        return self.response_ok(serializers.AdGroupRealtimeStatsSerializer(stats).data)
