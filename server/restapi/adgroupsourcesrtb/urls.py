from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^v1/adgroups/(?P<ad_group_id>\d+)/sources/rtb/$",
        views.AdGroupSourcesRTBViewSet.as_view({"get": "get", "put": "put"}),
        name="adgroups_sources_rtb_details",
    )
]
