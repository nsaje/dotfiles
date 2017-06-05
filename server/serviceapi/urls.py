from django.conf.urls import url

import views.video_upload_callback

urlpatterns = [
    url(
        r'^videoassets/(?P<videoasset_id>.+)$',
        views.video_upload_callback.VideoUploadCallbackView.as_view(),
        name='service.videoassets'
    ),
]
