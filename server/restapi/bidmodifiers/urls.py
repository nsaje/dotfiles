from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^v1/adgroups/(?P<ad_group_id>\d+)/bidmodifiers/$",
        views.BidModifierViewSet.as_view({"get": "list", "post": "create", "delete": "destroy"}),
        name="adgroups_bidmodifiers_list",
    ),
    url(
        r"^v1/adgroups/(?P<ad_group_id>\d+)/bidmodifiers/(?P<pk>\d+)$",
        views.BidModifierViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="adgroups_bidmodifiers_details",
    ),
]
