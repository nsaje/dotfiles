from django.conf.urls import url

from restapi.geolocation.v1 import views

app_name = "restapi.geolocation"
urlpatterns = [url(r"^$", views.GeolocationViewSet.as_view({"get": "list"}), name="geolocation_list")]
