from django.conf.urls import url

from . import views

app_name = "restapi.campaignbudget"
urlpatterns = [
    url(
        r"^(?P<campaign_id>\d+)/budgets/(?P<budget_id>\d+)$",
        views.CampaignBudgetViewSet.as_view({"get": "get", "put": "put"}),
        name="campaign_budgets_details",
    ),
    url(
        r"^(?P<campaign_id>\d+)/budgets/$",
        views.CampaignBudgetViewSet.as_view({"get": "list", "post": "create"}),
        name="campaign_budgets_list",
    ),
]
