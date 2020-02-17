from django.conf.urls import url

from . import views

app_name = "restapi.publishergroup"
urlpatterns = [
    url(
        r"^agencies/(?P<agency_id>\d+)/publishergroups/search/$",
        views.PublisherGroupSearchViewSet.as_view({"get": "list"}),
        name="publisher_group_search",
    )
]
