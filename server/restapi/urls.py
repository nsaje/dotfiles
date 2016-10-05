from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^campaigns/(?P<campaign_id>\d+)/settings/',
        views.CampaignViewDetails.as_view()
    ),
]
