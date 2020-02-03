from django.conf.urls import url

from . import views

app_name = "restapi.source"
urlpatterns = [url(r"^$", views.SourceViewSet.as_view({"get": "list"}), name="source_list")]
