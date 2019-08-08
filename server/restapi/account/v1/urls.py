from django.conf.urls import url

from . import views

app_name = "restapi.account"
urlpatterns = [
    url(r"^(?P<account_id>\d+)$", views.AccountViewSet.as_view({"get": "get", "put": "put"}), name="accounts_details"),
    url(r"^$", views.AccountViewSet.as_view({"get": "list", "post": "create"}), name="accounts_list"),
]
