from django.conf.urls import url

from . import views

app_name = "restapi.videoassets"
urlpatterns = [
    url(
        r"^(?P<account_id>\d+)/videoassets/$",
        views.VideoAssetListViewSet.as_view({"post": "post"}),
        name="videoassets_list",
    ),
    url(
        r"^(?P<account_id>\d+)/videoassets/(?P<videoasset_id>.+)$",
        views.VideoAssetViewSet.as_view({"get": "get", "put": "put"}),
        name="videoassets_details",
    ),
]
