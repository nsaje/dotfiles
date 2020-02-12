from rest_framework import permissions

import dash.features.realtimestats
import restapi.access
from restapi.adgroupsourcestats.v1 import serializers
from restapi.common.views_base import RESTAPIBaseViewSet


class AdGroupSourcesRealtimeStatsViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        stats = dash.features.realtimestats.get_ad_group_sources_stats(ad_group, use_local_currency=True)
        return self.response_ok(serializers.AdGroupSourcesRealtimeStatsSerializer(stats, many=True).data)
