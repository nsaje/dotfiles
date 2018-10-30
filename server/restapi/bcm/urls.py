from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url(
        r"^api/accounts/(?P<account_id>\d+)/credit/(?P<credit_id>\d+)/$",
        login_required(views.AccountCreditItemView.as_view()),
        name="accounts_credit_item",
    ),
    url(
        r"^api/accounts/(?P<account_id>\d+)/credit/$",
        login_required(views.AccountCreditView.as_view()),
        name="accounts_credit",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/budget/(?P<budget_id>\d+)/$",
        login_required(views.CampaignBudgetItemView.as_view()),
        name="campaigns_budget_item",
    ),
    url(
        r"^api/campaigns/(?P<campaign_id>\d+)/budget/$",
        login_required(views.CampaignBudgetView.as_view()),
        name="campaigns_budget",
    ),
]
