from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^campaigns/(?P<entity_id>\d+)$',
        views.CampaignViewDetails.as_view()
    ),
    url(
        r'^campaigns/$',
        views.CampaignViewList.as_view()
    ),
    url(
        r'^campaigns/(?P<campaign_id>\d+)/goals/(?P<goal_id>\d+)$',
        views.CampaignGoalsViewDetails.as_view()
    ),
    url(
        r'^campaigns/(?P<campaign_id>\d+)/goals/$',
        views.CampaignGoalsViewList.as_view()
    ),
    url(
        r'^adgroups/(?P<entity_id>\d+)$',
        views.AdGroupViewDetails.as_view()
    ),
    url(
        r'^adgroups/$',
        views.AdGroupViewList.as_view()
    ),
    url(
        r'^adgroups/(?P<ad_group_id>\d+)/sources/',
        views.AdGroupSourcesViewList.as_view()
    ),
    url(
        r'^adgroups/(?P<ad_group_id>\d+)/publishers/$',
        views.PublishersViewList.as_view()
    ),
    url(
        r'^contentads/batch/$',
        views.ContentAdBatchViewList.as_view()
    ),
    url(
        r'^contentads/batch/(?P<batch_id>\d+)$',
        views.ContentAdBatchViewDetails.as_view()
    ),
    url(
        r'^contentads/$',
        views.ContentAdViewList.as_view()
    ),
    url(
        r'^contentads/(?P<content_ad_id>\d+)$',
        views.ContentAdViewDetails.as_view()
    ),
]
