from django.conf.urls import url

from restapi.creditrefund.internal import views

app_name = "restapi.creditrefund"
urlpatterns = [
    url(
        r"^credits/(?P<credit_id>\d+)/refunds/(?P<refund_id>\d+)",
        views.CreditRefundViewSet.as_view({"get": "get", "delete": "remove"}),
        name="credits_refunds_details",
    ),
    url(
        r"^credits/(?P<credit_id>\d+)/refunds/$",
        views.CreditRefundViewSet.as_view({"get": "list", "post": "create"}),
        name="credits_refunds_list",
    ),
    url(r"^credits/refunds/$", views.CreditRefundViewSet.as_view({"get": "list"}), name="credits_refunds_list_all"),
]
