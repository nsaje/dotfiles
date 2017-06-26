from django.conf.urls import url

import views


urlpatterns = [
    url(
        r'internal/accounts/(?P<account_id>\d+)/campaignlauncher/validate$',
        views.CampaignLauncherViewSet.as_view({'post': 'validate'}),
        name='campaignlauncher_validate'
    ),
    url(
        r'internal/accounts/(?P<account_id>\d+)/campaignlauncher$',
        views.CampaignLauncherViewSet.as_view({'post': 'launch'}),
        name='campaignlauncher_launch'
    ),
]
