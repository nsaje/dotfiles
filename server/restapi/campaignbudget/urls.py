from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r'^v1/campaigns/(?P<campaign_id>\d+)/budgets/(?P<budget_id>\d+)$',
        views.CampaignBudgetViewSet.as_view({'get': 'get', 'put': 'put'}),
        name='campaign_budgets_details'
    ),
    url(
        r'^v1/campaigns/(?P<campaign_id>\d+)/budgets/$',
        views.CampaignBudgetViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='campaign_budgets_list'
    ),
]
