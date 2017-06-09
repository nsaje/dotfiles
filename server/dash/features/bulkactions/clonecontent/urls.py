from django.conf.urls import url

import views

urlpatterns = [
    url(
        r'^internal/contentads/batch/clone/$',
        views.CloneContentAds.as_view(),
        name='internal_content_ad_clone'
    ),
]
