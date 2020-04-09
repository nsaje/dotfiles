from django.conf.urls import url

from . import views

app_name = "restapi.publishergroup"
urlpatterns = [
    url(r"^publishergroups/$", views.PublisherGroupViewSet.as_view({"get": "list"}), name="publishergroup_list"),
    url(
        r"^publishergroups/(?P<publisher_group_id>\d+)/$",
        views.PublisherGroupViewSet.as_view({"delete": "remove"}),
        name="publishergroup_details",
    ),
]
