from django.conf.urls import url

from . import views

urlpatterns = [url(r"^internal/contentads/batch/clone/$", views.CloneContentAds.as_view(), name="content_ad_clone")]
