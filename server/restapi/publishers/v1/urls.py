from django.conf.urls import url

from restapi.publishers.v1 import views

app_name = "restapi.publishers"
urlpatterns = [
    url(
        r"^(?P<ad_group_id>\d+)/publishers/$",
        views.PublishersViewSet.as_view({"get": "list", "put": "put"}),
        name="publishers_list",
    )
]
