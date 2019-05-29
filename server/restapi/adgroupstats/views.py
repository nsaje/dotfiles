from django.http import Http404

import dash.features.realtimestats
import restapi.access
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers

REALTIME_STATS_AGENCIES = [
    55,  # Outbrain, nsaje, 7.12.2016
    78,  # Adtechnacity, nsaje, 12.5.2017
    33,  # inPowered, nsaje, 12.6.2017
    56,  # Feature Forward, nsaje, 29.5.2019
    448,  # ReigNN, nsaje, 29.5.2019
]


class AdGroupRealtimeStatsViewSet(RESTAPIBaseViewSet):
    """ Outbrain only """

    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)

        # agency check
        if ad_group.campaign.account.agency_id not in REALTIME_STATS_AGENCIES:
            raise Http404()

        stats = dash.features.realtimestats.get_ad_group_stats(ad_group)
        return self.response_ok(serializers.AdGroupRealtimeStatsSerializer(stats).data)
