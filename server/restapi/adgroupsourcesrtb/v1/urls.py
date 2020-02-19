from django.conf.urls import url

from restapi.adgroupsourcesrtb.v1 import views

app_name = "restapi.adgroupsourcesrtb"
urlpatterns = [
    url(
        r"^(?P<ad_group_id>\d+)/sources/rtb/$",
        views.AdGroupSourcesRTBViewSet.as_view({"get": "get", "put": "put"}),
        name="adgroups_sources_rtb_details",
    )
]
