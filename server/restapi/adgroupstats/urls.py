from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^v1/adgroups/(?P<ad_group_id>\d+)/realtimestats/$",
        views.AdGroupRealtimeStatsViewSet.as_view({"get": "get"}),
        name="adgroups_realtimestats",
    )
]
