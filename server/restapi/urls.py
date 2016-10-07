from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^campaigns/(?P<entity_id>\d+)',
        views.CampaignViewDetails.as_view()
    ),
    url(
        r'^campaigns/',
        views.CampaignViewList.as_view()
    ),
    url(
        r'^adgroups/(?P<entity_id>\d+)',
        views.AdGroupViewDetails.as_view()
    ),
    url(
        r'^adgroups/',
        views.AdGroupViewList.as_view()
    ),
]
