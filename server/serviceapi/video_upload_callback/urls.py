from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^videoassets/(?P<videoasset_id>.+)$", views.VideoUploadCallbackView.as_view(), name="service.videoassets")
]
