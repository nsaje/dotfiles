from django.conf.urls import url

from . import views

app_name = "restapi.creatives"
urlpatterns = [
    url(r"^(?P<creative_id>\d+)$", views.CreativeViewSet.as_view({"get": "get"}), name="creative_details"),
    url(r"^$", views.CreativeViewSet.as_view({"get": "list"}), name="creative_list"),
    url(r"^batch/$", views.CreativeBatchViewSet.as_view({"post": "create"}), name="creative_batch_list"),
    url(r"^batch/validate/$", views.CreativeBatchViewSet.as_view({"post": "validate"}), name="creative_batch_validate"),
    url(
        r"^batch/(?P<batch_id>\d+)$", views.CreativeBatchViewSet.as_view({"put": "put"}), name="creative_batch_details"
    ),
]
