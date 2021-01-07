from django.conf.urls import url

from . import views

app_name = "restapi.creatives"
urlpatterns = [
    url(r"^(?P<creative_id>\d+)$", views.CreativeViewSet.as_view({"get": "get"}), name="creative_details"),
    url(r"^$", views.CreativeViewSet.as_view({"get": "list"}), name="creative_list"),
]
