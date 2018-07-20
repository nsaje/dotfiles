from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r"^v1/adgroups/(?P<ad_group_id>\d+)/sources/$",
        views.AdGroupSourceViewSet.as_view({"get": "list", "put": "put", "post": "create"}),
        name="adgroups_sources_list",
    )
]
