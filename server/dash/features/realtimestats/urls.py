from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^v1/adgroups/(?P<ad_group_id>\d+)/realtimestats/$',
        views.AdGroupRealtimeStatsView.as_view(),
        name='adgroups_realtimestats'
    ),
    url(
        r'^v1/adgroups/(?P<ad_group_id>\d+)/realtimestats/sources/$',
        views.AdGroupSourcesRealtimeStatsView.as_view(),
        name='adgroups_realtimestats_sources'
    ),
]
