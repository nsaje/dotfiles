from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^v1/accounts/(?P<account_id>\d+)/videoassets/$',
        views.VideoAssetListView.as_view(),
        name='videoassets_list'
    ),
    url(
        r'^v1/accounts/(?P<account_id>\d+)/videoassets/(?P<videoasset_id>.+)$',
        views.VideoAssetView.as_view(),
        name='videoassets_details'
    ),
]
