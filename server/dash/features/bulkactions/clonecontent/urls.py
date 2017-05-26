from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^v1/contentads/batch/clone/$',
        views.CloneContentAds.as_view(),
        name='content_ad_clone'
    ),
    url(
        r'^internal/contentads/batch/clone/$',
        views.InternalCloneContentAds.as_view(),
        name='internal_content_ad_clone'
    ),
]
