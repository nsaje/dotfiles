from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r'^v1/campaigns/(?P<campaign_id>\d+)$',
        views.CampaignViewSet.as_view({'get': 'get', 'put': 'put'}),
        name='campaigns_details'
    ),
    url(
        r'^v1/campaigns/$',
        views.CampaignViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='campaigns_list'
    ),
]
