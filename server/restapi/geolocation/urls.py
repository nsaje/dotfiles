from django.conf.urls import url

from . import views


urlpatterns = [url(r"^v1/geolocations/$", views.GeolocationViewSet.as_view({"get": "list"}), name="geolocation_list")]
