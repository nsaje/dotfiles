from django.conf.urls import url

from . import views

app_name = "restapi.adgroup"
urlpatterns = [
    url(r"^(?P<ad_group_id>\d+)$", views.AdGroupViewSet.as_view({"get": "get", "put": "put"}), name="adgroups_details"),
    url(r"^$", views.AdGroupViewSet.as_view({"get": "list", "post": "create"}), name="adgroups_list"),
]
