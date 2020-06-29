from django.conf.urls import url

from . import views

app_name = "restapi.contentad"
urlpatterns = [
    url(r"^batch/clone/$", views.CloneContentAdsViewSet.as_view({"post": "post"}), name="content_ads_batch_clone")
]
