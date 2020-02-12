from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^v1/accounts/(?P<account_id>\d+)/audiences/(?P<audience_id>\d+)$",
        views.AudienceViewSet.as_view({"get": "get", "put": "put"}),
        name="audiences_details",
    ),
    url(
        r"^v1/accounts/(?P<account_id>\d+)/audiences/$",
        views.AudienceViewSet.as_view({"get": "list", "post": "create"}),
        name="audiences_list",
    ),
]
