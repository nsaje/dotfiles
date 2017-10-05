from django.conf.urls import url

import views


urlpatterns = [
    url(
        r'^v1/accounts/(?P<account_id>\d+)$',
        views.AccountViewSet.as_view({'get': 'get', 'put': 'put'}),
        name='accounts_details'
    ),
    url(
        r'^v1/accounts/$',
        views.AccountViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='accounts_list'
    ),
]
