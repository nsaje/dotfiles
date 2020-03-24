from django.conf.urls import url

from . import views

app_name = "restapi.publishergroup"
urlpatterns = [
    url(
        r"^publishergroups/agencies/(?P<agency_id>\d+)/search/$",
        views.PublisherGroupSearchViewSet.as_view({"get": "list"}),
        name="publisher_group_search",
    ),
    url(
        r"^publishergroups/(?P<publisher_group_id>\d+)/$",
        views.PublisherGroupViewSet.as_view({"delete": "delete"}),
        name="publisher_group",
    ),
]
