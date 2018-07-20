from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r"^v1/adgroups/(?P<ad_group_id>\d+)/realtimestats/sources/$",
        views.AdGroupSourcesRealtimeStatsViewSet.as_view({"get": "list"}),
        name="adgroups_realtimestats_sources",
    )
]
