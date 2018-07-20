from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r"^v1/adgroups/(?P<ad_group_id>\d+)/publishers/$",
        views.PublishersViewSet.as_view({"get": "list", "put": "put"}),
        name="publishers_list",
    )
]
