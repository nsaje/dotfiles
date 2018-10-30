from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^v1/contentads/batch/$", views.ContentAdBatchViewList.as_view(), name="contentads_batch_list"),
    url(
        r"^v1/contentads/batch/(?P<batch_id>\d+)$",
        views.ContentAdBatchViewDetails.as_view(),
        name="contentads_batch_details",
    ),
    url(r"^v1/contentads/$", views.ContentAdViewList.as_view(), name="contentads_list"),
    url(r"^v1/contentads/(?P<content_ad_id>\d+)$", views.ContentAdViewDetails.as_view(), name="contentads_details"),
]
