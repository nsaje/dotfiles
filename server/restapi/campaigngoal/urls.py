from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r"^v1/campaigns/(?P<campaign_id>\d+)/goals/(?P<goal_id>\d+)$",
        views.CampaignGoalViewSet.as_view({"get": "get", "put": "put", "delete": "remove"}),
        name="campaigngoals_details",
    ),
    url(
        r"^v1/campaigns/(?P<campaign_id>\d+)/goals/$",
        views.CampaignGoalViewSet.as_view({"get": "list", "post": "create"}),
        name="campaigngoals_list",
    ),
]
