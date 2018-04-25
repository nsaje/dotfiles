from django.conf.urls import url

from . import views
import restapi.views.realtimestats
import restapi.adgroupsource.views
import restapi.publishers.views
from . import geolocation
import dash.features.videoassets.urls
import dash.features.bluekai.urls
from dash.features.bulkactions import clonecontent
from dash.features import cloneadgroup
import restapi.campaignlauncher.urls
import restapi.bcm.urls
import restapi.inventory_planning.urls
import restapi.account.urls
import restapi.accountcredit.urls
import restapi.campaign.urls
import restapi.adgroup.urls
import restapi.contentad.urls

urlpatterns = [
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
        r'^v1/adgroups/(?P<ad_group_id>\d+)/sources/$',
        restapi.adgroupsource.views.AdGroupSourcesViewList.as_view(),
        name='adgroups_sources_list'
    ),
    url(
        r'^v1/adgroups/(?P<ad_group_id>\d+)/sources/rtb/$',
        views.AdGroupSourcesRTBViewDetails.as_view(),
        name='adgroups_sources_rtb_details'
    ),
    url(
        r'^v1/adgroups/(?P<ad_group_id>\d+)/publishers/$',
        restapi.publishers.views.PublishersViewList.as_view(),
        name='publishers_list'
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
    url(
        r'^v1/adgroups/(?P<ad_group_id>\d+)/realtimestats/$',
        restapi.views.realtimestats.AdGroupRealtimeStatsView.as_view(),
        name='adgroups_realtimestats'
    ),
    url(
        r'^v1/adgroups/(?P<ad_group_id>\d+)/realtimestats/sources/$',
        restapi.views.realtimestats.AdGroupSourcesRealtimeStatsView.as_view(),
        name='adgroups_realtimestats_sources'
    ),
]

urlpatterns += restapi.account.urls.urlpatterns
urlpatterns += restapi.accountcredit.urls.urlpatterns
urlpatterns += restapi.campaign.urls.urlpatterns
urlpatterns += restapi.adgroup.urls.urlpatterns
urlpatterns += restapi.contentad.urls.urlpatterns
urlpatterns += clonecontent.urls.urlpatterns
urlpatterns += cloneadgroup.urls.urlpatterns
urlpatterns += dash.features.videoassets.urls.urlpatterns
urlpatterns += dash.features.bluekai.urls.urlpatterns
urlpatterns += restapi.campaignlauncher.urls.urlpatterns
urlpatterns += restapi.bcm.urls.urlpatterns
urlpatterns += restapi.inventory_planning.urls.urlpatterns
