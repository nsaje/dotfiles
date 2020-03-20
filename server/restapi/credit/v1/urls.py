from django.conf.urls import url

from . import views

app_name = "restapi.credit"
urlpatterns = [
    url(
        r"^accounts/(?P<account_id>\d+)/credits/(?P<credit_id>\d+)$",
        views.CreditViewSet.as_view({"get": "get"}),
        name="credits_details",
    ),
    url(r"^accounts/(?P<account_id>\d+)/credits/$", views.CreditViewSet.as_view({"get": "list"}), name="credits_list"),
]
