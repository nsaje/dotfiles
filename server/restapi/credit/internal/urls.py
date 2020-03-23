from django.conf.urls import url

from . import views

app_name = "restapi.credit"
urlpatterns = [
    url(
        r"^credits/(?P<credit_id>\d+)$",
        views.CreditViewSet.as_view({"get": "get", "put": "put"}),
        name="credits_details",
    ),
    url(
        r"^credits/(?P<credit_id>\d+)/budgets/$",
        views.CreditViewSet.as_view({"get": "list_budgets"}),
        name="credit_budgets_list",
    ),
    url(r"^credits/$", views.CreditViewSet.as_view({"get": "list", "post": "create"}), name="credits_list"),
    url(r"^credits/totals/$", views.CreditViewSet.as_view({"get": "totals"}), name="credits_totals"),
]
