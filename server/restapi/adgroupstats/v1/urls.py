from django.conf.urls import url

from restapi.adgroupstats.v1 import views

app_name = "restapi.addgroupstats"
urlpatterns = [
    url(
        r"^(?P<ad_group_id>\d+)/realtimestats/$",
        views.AdGroupRealtimeStatsViewSet.as_view({"get": "get"}),
        name="adgroups_realtimestats",
    )
]
