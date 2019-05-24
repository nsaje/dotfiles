from django.conf.urls import url

from . import views

app_name = "restapi.campaign"
urlpatterns = [
    url(
        r"^(?P<campaign_id>\d+)$", views.CampaignViewSet.as_view({"get": "get", "put": "put"}), name="campaigns_details"
    ),
    url(r"^$", views.CampaignViewSet.as_view({"get": "list", "post": "create"}), name="campaigns_list"),
    url(r"^validate/$", views.CampaignViewSet.as_view({"post": "validate"}), name="campaigns_validate"),
    url(r"^defaults/$", views.CampaignViewSet.as_view({"get": "defaults"}), name="campaigns_defaults"),
]
