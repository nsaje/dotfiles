from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^v1/adgroups/clone/$',
        views.CloneAdGroup.as_view(),
        name='ad_group_clone'
    ),
]
