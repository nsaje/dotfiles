from django.conf.urls import url

from . import views

app_name = "restapi.campaign"
urlpatterns = [
    url(
        r"^(?P<campaign_id>\d+)$", views.CampaignViewSet.as_view({"get": "get", "put": "put"}), name="campaigns_details"
    ),
    url(r"^$", views.CampaignViewSet.as_view({"get": "list", "post": "create"}), name="campaigns_list"),
]
