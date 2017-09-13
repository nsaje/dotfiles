from django.conf.urls import url

import views
import adgroupsource.views
import publishers.views
import geolocation
import dash.features.videoassets.urls
import dash.features.bluekai.urls
from dash.features.bulkactions import clonecontent
from dash.features import cloneadgroup
from dash.features import realtimestats
import campaignlauncher.urls
import bcm.urls

urlpatterns = [
    url(
        r'^v1/accounts/(?P<entity_id>\d+)$',
        views.AccountViewDetails.as_view(),
        name='accounts_details'
    ),
    url(
        r'^v1/accounts/$',
        views.AccountViewList.as_view(),
        name='accounts_list'
    ),
    url(
        r'^v1/accounts/(?P<account_id>\d+)/credits/$',
        views.AccountCreditViewList.as_view(),
        name='accounts_credits_list'
    ),
    url(
        r'^v1/campaigns/(?P<entity_id>\d+)$',
        views.CampaignViewDetails.as_view(),
        name='campaigns_details'
    ),
    url(
        r'^v1/campaigns/$',
        views.CampaignViewList.as_view(),
        name='campaigns_list'
    ),
    url(
        r'^v1/campaigns/(?P<campaign_id>\d+)/stats/$',
        views.CampaignStatsView.as_view(),
        name='campaignstats'
    ),
    url(
        r'^v1/campaigns/(?P<campaign_id>\d+)/goals/(?P<goal_id>\d+)$',
        views.CampaignGoalsViewDetails.as_view(),
        name='campaigngoals_details'
    ),
    url(
        r'^v1/campaigns/(?P<campaign_id>\d+)/goals/$',
        views.CampaignGoalsViewList.as_view(),
        name='campaigngoals_list'
    ),
    url(
        r'^v1/campaigns/(?P<campaign_id>\d+)/budgets/$',
        views.CampaignBudgetViewList.as_view(),
        name='campaigns_budget_list'
    ),
    url(
        r'^v1/campaigns/(?P<campaign_id>\d+)/budgets/(?P<budget_id>\d+)$',
        views.CampaignBudgetViewDetails.as_view(),
        name='campaigns_budget_details'
    ),
    url(
        r'^v1/adgroups/(?P<entity_id>\d+)$',
        views.AdGroupViewDetails.as_view(),
        name='adgroups_details'
    ),
    url(
        r'^v1/adgroups/$',
        views.AdGroupViewList.as_view(),
        name='adgroups_list'
    ),
    url(
        r'^v1/adgroups/(?P<ad_group_id>\d+)/sources/$',
        adgroupsource.views.AdGroupSourcesViewList.as_view(),
        name='adgroups_sources_list'
    ),
    url(
        r'^v1/adgroups/(?P<ad_group_id>\d+)/sources/rtb/$',
        views.AdGroupSourcesRTBViewDetails.as_view(),
        name='adgroups_sources_rtb_details'
    ),
    url(
        r'^v1/adgroups/(?P<ad_group_id>\d+)/publishers/$',
        publishers.views.PublishersViewList.as_view(),
        name='publishers_list'
    ),
    url(
        r'^v1/contentads/batch/$',
        views.ContentAdBatchViewList.as_view(),
        name='contentads_batch_list'
    ),
    url(
        r'^v1/contentads/batch/(?P<batch_id>\d+)$',
        views.ContentAdBatchViewDetails.as_view(),
        name='contentads_batch_details'
    ),
    url(
        r'^v1/contentads/$',
        views.ContentAdViewList.as_view(),
        name='contentads_list'
    ),
    url(
        r'^v1/contentads/(?P<content_ad_id>\d+)$',
        views.ContentAdViewDetails.as_view(),
        name='contentads_details'
    ),
    url(
        r'^v1/reports/$',
        views.ReportsViewList.as_view(),
        name='reports_list'
    ),
    url(
        r'^v1/reports/(?P<job_id>\d+)$',
        views.ReportsViewDetails.as_view(),
        name='reports_details'
    ),
    url(
        r'^v1/accounts/(?P<account_id>\d+)/publishergroups/$',
        views.PublisherGroupViewSet.as_view(actions={'get': 'list', 'post': 'create'}),
        name='publisher_group_list'
    ),
    url(
        r'^v1/accounts/(?P<account_id>\d+)/publishergroups/(?P<publisher_group_id>\d+)$',
        views.PublisherGroupViewSet.as_view(actions={
            'get': 'retrieve', 'put': 'partial_update', 'delete': 'destroy'}),
        name='publisher_group_details'
    ),
    url(
        r'^v1/publishergroups/(?P<publisher_group_id>\d+)/entries/$',
        views.PublisherGroupEntryViewSet.as_view(actions={'get': 'list', 'post': 'create'}),
        name='publisher_group_entry_list'
    ),
    url(
        r'^v1/publishergroups/(?P<publisher_group_id>\d+)/entries/(?P<entry_id>\d+)$',
        views.PublisherGroupEntryViewSet.as_view(actions={
            'get': 'retrieve', 'delete': 'destroy', 'put': 'partial_update'}),
        name='publisher_group_entry_details'
    ),
    url(
        r'^v1/geolocations/$',
        geolocation.GeolocationListView.as_view(),
        name='geolocation_list'
    ),
]

urlpatterns += clonecontent.urls.urlpatterns
urlpatterns += cloneadgroup.urls.urlpatterns
urlpatterns += dash.features.videoassets.urls.urlpatterns
urlpatterns += dash.features.bluekai.urls.urlpatterns
urlpatterns += realtimestats.urls.urlpatterns
urlpatterns += campaignlauncher.urls.urlpatterns
urlpatterns += bcm.urls.urlpatterns
