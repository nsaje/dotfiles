from django.conf.urls import url

from . import views

app_name = "restapi.user"
urlpatterns = [
    url(r"^$", views.UserViewSet.as_view({"get": "list", "post": "create"}), name="user_list"),
    url(
        r"^(?P<user_id>\d+)$",
        views.UserViewSet.as_view({"get": "get", "put": "put", "delete": "remove"}),
        name="user_details",
    ),
    url(r"^(?P<user_id>\d+)/resendemail/$", views.UserViewSet.as_view({"put": "resendemail"}), name="user_resendemail"),
    url(r"^validate/$", views.UserViewSet.as_view({"post": "validate"}), name="user_validate"),
]
