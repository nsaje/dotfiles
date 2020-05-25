import dash.features.realtimestats
import zemauth.access
from restapi.adgroupstats.v1 import serializers
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission


class AdGroupRealtimeStatsViewSet(RESTAPIBaseViewSet):
    """ Outbrain only """

    def get(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)

        stats = dash.features.realtimestats.get_ad_group_stats(ad_group)
        return self.response_ok(serializers.AdGroupRealtimeStatsSerializer(stats).data)
