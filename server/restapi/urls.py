from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^accounts/(?P<account_id>\d+)/credits/$',
        views.AccountCreditViewList.as_view(),
        name='accounts_credits_list'
    ),
    url(
        r'^campaigns/(?P<entity_id>\d+)$',
        views.CampaignViewDetails.as_view(),
        name='campaigns_details'
    ),
    url(
        r'^campaigns/$',
        views.CampaignViewList.as_view(),
        name='campaigns_list'
    ),
    url(
        r'^campaigns/(?P<campaign_id>\d+)/goals/(?P<goal_id>\d+)$',
        views.CampaignGoalsViewDetails.as_view(),
        name='campaigngoals_details'
    ),
    url(
        r'^campaigns/(?P<campaign_id>\d+)/goals/$',
        views.CampaignGoalsViewList.as_view(),
        name='campaigngoals_list'
    ),
    url(
        r'^campaigns/(?P<campaign_id>\d+)/budgets/$',
        views.CampaignBudgetViewList.as_view(),
        name='campaigns_budget_list'
    ),
    url(
        r'^campaigns/(?P<campaign_id>\d+)/budgets/(?P<budget_id>\d+)$',
        views.CampaignBudgetViewDetails.as_view(),
        name='campaigns_budget_details'
    ),
    url(
        r'^adgroups/(?P<entity_id>\d+)$',
        views.AdGroupViewDetails.as_view(),
        name='adgroups_details'
    ),
    url(
        r'^adgroups/$',
        views.AdGroupViewList.as_view(),
        name='adgroups_list'
    ),
    url(
        r'^adgroups/(?P<ad_group_id>\d+)/sources/$',
        views.AdGroupSourcesViewList.as_view(),
        name='adgroups_sources_list'
    ),
    url(
        r'^adgroups/(?P<ad_group_id>\d+)/sources/rtb/$',
        views.AdGroupSourcesRTBViewDetails.as_view(),
        name='adgroups_sources_rtb_details'
    ),
    url(
        r'^adgroups/(?P<ad_group_id>\d+)/publishers/$',
        views.PublishersViewList.as_view(),
        name='publishers_list'
    ),
    url(
        r'^contentads/batch/$',
        views.ContentAdBatchViewList.as_view(),
        name='contentads_batch_list'
    ),
    url(
        r'^contentads/batch/(?P<batch_id>\d+)$',
        views.ContentAdBatchViewDetails.as_view(),
        name='contentads_batch_details'
    ),
    url(
        r'^contentads/$',
        views.ContentAdViewList.as_view(),
        name='contentads_list'
    ),
    url(
        r'^contentads/(?P<content_ad_id>\d+)$',
        views.ContentAdViewDetails.as_view(),
        name='contentads_details'
    ),
    url(
        r'^reports/$',
        views.ReportsViewList.as_view(),
        name='reports_list'
    ),
    url(
        r'^reports/(?P<job_id>\d+)$',
        views.ReportsViewDetails.as_view(),
        name='reports_details'
    ),
]
