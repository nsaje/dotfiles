from django.conf.urls import url

from . import views

app_name = "restapi.accountcredit"
urlpatterns = [
    url(
        r"^(?P<account_id>\d+)/credits/(?P<credit_id>\d+)$",
        views.AccountCreditViewSet.as_view({"get": "get"}),
        name="accounts_credits_details",
    ),
    url(
        r"^(?P<account_id>\d+)/credits/$",
        views.AccountCreditViewSet.as_view({"get": "list"}),
        name="accounts_credits_list",
    ),
]
