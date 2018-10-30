from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^v1/adgroups/(?P<ad_group_id>\d+)$",
        views.AdGroupViewSet.as_view({"get": "get", "put": "put"}),
        name="adgroups_details",
    ),
    url(r"^v1/adgroups/$", views.AdGroupViewSet.as_view({"get": "list", "post": "create"}), name="adgroups_list"),
]
