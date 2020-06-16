from django.conf.urls import url

from . import views

app_name = "restapi.adgroup"
urlpatterns = [
    url(r"^(?P<ad_group_id>\d+)$", views.AdGroupViewSet.as_view({"get": "get", "put": "put"}), name="adgroups_details"),
    url(r"^(?P<ad_group_id>\d+)/alerts$", views.AdGroupViewSet.as_view({"get": "alerts"}), name="adgroups_alerts"),
    url(r"^$", views.AdGroupViewSet.as_view({"get": "list", "post": "create"}), name="adgroups_list"),
    url(r"^validate/$", views.AdGroupViewSet.as_view({"post": "validate"}), name="adgroups_validate"),
    url(r"^defaults/$", views.AdGroupViewSet.as_view({"get": "defaults"}), name="adgroups_defaults"),
]
