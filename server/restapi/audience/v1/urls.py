from django.conf.urls import url

from restapi.audience.v1 import views

app_name = "restapi.audience"
urlpatterns = [
    url(
        r"^(?P<account_id>\d+)/audiences/(?P<audience_id>\d+)$",
        views.AudienceViewSet.as_view({"get": "get", "put": "put"}),
        name="audiences_details",
    ),
    url(
        r"^(?P<account_id>\d+)/audiences/$",
        views.AudienceViewSet.as_view({"get": "list", "post": "create"}),
        name="audiences_list",
    ),
]
