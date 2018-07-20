from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r"^v1/campaigns/(?P<campaign_id>\d+)/stats/$",
        views.CampaignStatsViewSet.as_view({"get": "get"}),
        name="campaignstats",
    )
]
