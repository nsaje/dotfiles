from django.conf.urls import url

from restapi.adgroupsourcestats.v1 import views

app_name = "restapi.adgroupsourcestats"
urlpatterns = [
    url(
        r"^v1/adgroups/(?P<ad_group_id>\d+)/realtimestats/sources/$",
        views.AdGroupSourcesRealtimeStatsViewSet.as_view({"get": "list"}),
        name="adgroups_realtimestats_sources",
    )
]
