from django.conf.urls import url

from restapi.publishergroupentry.v1 import views

app_name = "restapi.publishergroupentry"
urlpatterns = [
    url(
        r"^(?P<publisher_group_id>\d+)/entries/(?P<entry_id>\d+)$",
        views.PublisherGroupEntryViewSet.as_view({"get": "retrieve", "put": "partial_update", "delete": "destroy"}),
        name="publisher_group_entry_details",
    ),
    url(
        r"^(?P<publisher_group_id>\d+)/entries/$",
        views.PublisherGroupEntryViewSet.as_view({"get": "list", "post": "create"}),
        name="publisher_group_entry_list",
    ),
]
