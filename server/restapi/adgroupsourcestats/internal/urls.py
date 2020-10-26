from django.conf.urls import url

from restapi.adgroupsourcestats.internal import views

app_name = "restapi.adgroupsourcestats"
urlpatterns = [
    url(
        r"^(?P<ad_group_id>\d+)/realtimestats/sources/$",
        views.InternalAdGroupSourcesRealtimeStatsViewSet.as_view({"get": "get"}),
        name="adgroups_realtimestats_sources",
    )
]
