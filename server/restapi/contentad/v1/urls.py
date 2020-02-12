from django.conf.urls import url

from restapi.contentad.v1 import views

app_name = "restapi.contentad"
urlpatterns = [
    url(r"^batch/$", views.ContentAdBatchViewList.as_view(), name="contentads_batch_list"),
    url(r"^batch/(?P<batch_id>\d+)$", views.ContentAdBatchViewDetails.as_view(), name="contentads_batch_details"),
    url(r"^$", views.ContentAdViewList.as_view(), name="contentads_list"),
    url(r"^(?P<content_ad_id>\d+)$", views.ContentAdViewDetails.as_view(), name="contentads_details"),
]
