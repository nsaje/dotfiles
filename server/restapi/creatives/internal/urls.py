from django.conf.urls import url

from . import views

app_name = "restapi.creatives"
urlpatterns = [
    url(r"^(?P<creative_id>\d+)$", views.CreativeViewSet.as_view({"get": "get"}), name="creative_details"),
    url(r"^$", views.CreativeViewSet.as_view({"get": "list"}), name="creative_list"),
    url(r"^batch/$", views.CreativeBatchViewSet.as_view({"post": "create"}), name="creative_batch_list"),
    url(r"^batch/validate/$", views.CreativeBatchViewSet.as_view({"post": "validate"}), name="creative_batch_validate"),
    url(
        r"^batch/(?P<batch_id>\d+)$",
        views.CreativeBatchViewSet.as_view({"get": "get", "put": "put"}),
        name="creative_batch_details",
    ),
    url(
        r"^batch/(?P<batch_id>\d+)/upload/$",
        views.CreativeBatchViewSet.as_view({"post": "upload"}),
        name="creative_batch_upload",
    ),
    url(
        r"^batch/(?P<batch_id>\d+)/candidates/$",
        views.CreativeCandidateViewSet.as_view({"get": "list", "post": "create"}),
        name="creative_candidate_list",
    ),
    url(
        r"^batch/(?P<batch_id>\d+)/candidates/(?P<candidate_id>\d+)$",
        views.CreativeCandidateViewSet.as_view({"get": "get", "put": "put", "delete": "remove"}),
        name="creative_candidate_details",
    ),
]
