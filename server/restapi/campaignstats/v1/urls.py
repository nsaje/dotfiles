from django.conf.urls import url

from restapi.campaignstats.v1 import views

app_name = "restapi.campaignstats"
urlpatterns = [
    url(
        r"^v1/campaigns/(?P<campaign_id>\d+)/stats/$",
        views.CampaignStatsViewSet.as_view({"get": "get"}),
        name="campaignstats",
    )
]
