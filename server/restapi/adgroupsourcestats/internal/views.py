from rest_framework import permissions

import dash.features.realtimestats
import zemauth.access
from restapi.adgroupsourcestats.internal import serializers
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission


class InternalAdGroupSourcesRealtimeStatsViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, ad_group_id):
        ad_group = zemauth.access.get_ad_group(request.user, Permission.READ, ad_group_id)

        stats = dash.features.realtimestats.get_ad_group_sources_stats(ad_group, use_local_currency=True)
        return self.response_ok(serializers.InternalAdGroupSourcesRealtimeStatsSerializer(stats).data)
