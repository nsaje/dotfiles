from django.http import Http404
from rest_framework import permissions

from restapi.views import RESTAPIBaseView

from dash.views import helpers

import serializers
import service

REALTIME_STATS_AGENCIES = [
    55,  # Outbrain, nsaje, 7.12.2016
    78,  # Adtechnacity, nsaje, 12.5.2017
    33,  # inPowered, nsaje, 12.6.2017
]


class AdGroupRealtimeStatsView(RESTAPIBaseView):
    """ Outbrain only """

    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

        # agency check
        if ad_group.campaign.account.agency_id not in REALTIME_STATS_AGENCIES:
            raise Http404()

        stats = service.get_ad_group_stats(ad_group)
        return self.response_ok(serializers.AdGroupRealtimeStatsSerializer(stats).data)


class AdGroupSourcesRealtimeStatsView(RESTAPIBaseView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

        stats = service.get_ad_group_sources_stats(ad_group)
        return self.response_ok(
            serializers.AdGroupSourcesRealtimeStatsSerializer(stats, many=True).data,
        )
