from django.conf.urls import url

from . import views

app_name = "restapi.publishergroup"
urlpatterns = [
    url(
        r"^accounts/(?P<account_id>\d+)/publishergroups/(?P<publisher_group_id>\d+)$",
        views.PublisherGroupViewSet.as_view({"get": "retrieve", "put": "partial_update", "delete": "destroy"}),
        name="publisher_group_details",
    ),
    url(
        r"^accounts/(?P<account_id>\d+)/publishergroups/$",
        views.PublisherGroupViewSet.as_view({"get": "list", "post": "create"}),
        name="publisher_group_list",
    ),
]
