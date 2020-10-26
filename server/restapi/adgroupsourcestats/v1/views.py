from rest_framework import permissions

import dash.features.realtimestats
import zemauth.access
from restapi.adgroupsourcestats.v1 import serializers
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission


class AdGroupSourcesRealtimeStatsViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)

        stats = dash.features.realtimestats.get_ad_group_sources_stats(ad_group, use_local_currency=True)["spend"]
        return self.response_ok(serializers.AdGroupSourcesRealtimeStatsSerializer(stats, many=True).data)
