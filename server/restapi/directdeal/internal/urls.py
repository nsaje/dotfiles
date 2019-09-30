from django.conf.urls import url

from . import views

app_name = "restapi.directdeal"
urlpatterns = [
    url(
        r"^(?P<deal_id>\d+)$",
        views.DirectDealViewSet.as_view({"get": "get", "put": "put", "delete": "remove"}),
        name="directdeal_details",
    ),
    url(r"^$", views.DirectDealViewSet.as_view({"get": "list", "post": "create"}), name="directdeal_list"),
    url(r"^validate/$", views.DirectDealViewSet.as_view({"post": "validate"}), name="directdeal_validate"),
    url(
        r"^(?P<deal_id>\d+)/connections/$",
        views.DirectDealViewSet.as_view({"get": "list_connections"}),
        name="directdealconnection_list",
    ),
    url(
        r"^(?P<deal_id>\d+)/connections/(?P<deal_connection_id>\d+)$",
        views.DirectDealViewSet.as_view({"delete": "remove_connection"}),
        name="directdealconnection_details",
    ),
]
