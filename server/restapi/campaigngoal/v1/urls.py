from django.conf.urls import url

from restapi.campaigngoal.v1 import views

app_name = "restapi.campaigngoal"
urlpatterns = [
    url(
        r"^(?P<campaign_id>\d+)/goals/(?P<goal_id>\d+)$",
        views.CampaignGoalViewSet.as_view({"get": "get", "put": "put", "delete": "remove"}),
        name="campaigngoals_details",
    ),
    url(
        r"^(?P<campaign_id>\d+)/goals/$",
        views.CampaignGoalViewSet.as_view({"get": "list", "post": "create"}),
        name="campaigngoals_list",
    ),
]
