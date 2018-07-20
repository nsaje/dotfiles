from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r"internal/accounts/(?P<account_id>\d+)/credit/(?P<credit_id>\d+)/refunds/(?P<refund_id>\d+)",
        views.AccountCreditRefundViewSet.as_view({"get": "get", "delete": "remove"}),
        name="accounts_credits_refunds_details",
    ),
    url(
        r"internal/accounts/(?P<account_id>\d+)/credit/(?P<credit_id>\d+)/refunds/$",
        views.AccountCreditRefundViewSet.as_view({"get": "list", "post": "create"}),
        name="accounts_credits_refunds_list",
    ),
    url(
        r"internal/accounts/(?P<account_id>\d+)/credit/refunds/$",
        views.AccountCreditRefundViewSet.as_view({"get": "list"}),
        name="accounts_credits_refunds_list_all",
    ),
]
