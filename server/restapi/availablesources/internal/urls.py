from django.conf.urls import url

from . import views

app_name = "restapi.source"
urlpatterns = [url(r"^(?P<agency_id>\d+)/sources/$", views.SourceViewSet.as_view({"get": "list"}), name="source_list")]
