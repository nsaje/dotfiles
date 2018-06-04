from django.conf import settings
from restapi.common.views_base import RESTAPIBaseViewSet
import restapi.access

import dash.features.realtimestats
from rest_framework import permissions

from . import serializers


class AdGroupSourcesRealtimeStatsViewSet(RESTAPIBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        stats = dash.features.realtimestats.get_ad_group_sources_stats(
            ad_group,
            use_local_currency=request.user.has_perm('zemauth.can_see_infobox_in_local_currency'),
        )
        return self.response_ok(
            serializers.AdGroupSourcesRealtimeStatsSerializer(stats, many=True).data,
        )
