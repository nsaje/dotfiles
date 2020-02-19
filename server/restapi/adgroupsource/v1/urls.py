from django.conf.urls import url

from restapi.adgroupsource.v1 import views

app_name = "restapi.adgroupsource"
urlpatterns = [
    url(
        r"^(?P<ad_group_id>\d+)/sources/$",
        views.AdGroupSourceViewSet.as_view({"get": "list", "put": "put", "post": "create"}),
        name="adgroups_sources_list",
    )
]
