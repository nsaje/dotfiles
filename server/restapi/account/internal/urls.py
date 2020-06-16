from django.conf.urls import url

from . import views

app_name = "restapi.account"
urlpatterns = [
    url(r"^(?P<account_id>\d+)$", views.AccountViewSet.as_view({"get": "get", "put": "put"}), name="accounts_details"),
    url(r"^(?P<account_id>\d+)/alerts$", views.AccountViewSet.as_view({"get": "alerts"}), name="accounts_alerts"),
    url(r"^$", views.AccountViewSet.as_view({"get": "list", "post": "create"}), name="accounts_list"),
    url(r"^validate/$", views.AccountViewSet.as_view({"post": "validate"}), name="accounts_validate"),
    url(r"^defaults/$", views.AccountViewSet.as_view({"get": "defaults"}), name="accounts_defaults"),
    url(r"^alerts$", views.AccountViewSet.as_view({"get": "alerts"}), name="accounts_all_alerts"),
]
