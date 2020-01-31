from django.conf.urls import url

from . import views

app_name = "restapi.agency"
urlpatterns = [url(r"^$", views.AgencyViewSet.as_view({"get": "list"}), name="agencies_list")]
