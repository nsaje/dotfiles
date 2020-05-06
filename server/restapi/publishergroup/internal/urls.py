from django.conf.urls import url

from core.features.publisher_groups import CONNECTION_TYPE_MAP

from . import views

allowed_locations = "|".join(CONNECTION_TYPE_MAP.keys())

app_name = "restapi.publishergroup"
urlpatterns = [
    url(r"^publishergroups/$", views.PublisherGroupViewSet.as_view({"get": "list"}), name="publishergroup_list"),
    url(
        r"^publishergroups/(?P<publisher_group_id>\d+)/$",
        views.PublisherGroupViewSet.as_view({"delete": "remove"}),
        name="publishergroup_details",
    ),
    url(
        r"^publishergroups/(?P<publisher_group_id>\d+)/connections/$",
        views.PublisherGroupConnectionsViewSet.as_view({"get": "list_connections"}),
        name="publishergroup_connections",
    ),
    url(
        r"^publishergroups/(?P<publisher_group_id>\d+)/connections/(?P<location>("
        + allowed_locations
        + r")+)/(?P<entity_id>\d+)$",
        views.PublisherGroupConnectionsViewSet.as_view({"delete": "remove_connection"}),
        name="remove_publishergroup_connection",
    ),
    url(
        r"^publishergroups/add/$",
        views.AddToPublisherGroupViewSet.as_view({"post": "create"}),
        name="publishergroup_add",
    ),
]
