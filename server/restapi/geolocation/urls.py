from django.conf.urls import include
from django.conf.urls import url

import restapi.geolocation.v1.urls

urlpatterns = [url(r"^v1/geolocations/", include(restapi.geolocation.v1.urls, namespace="restapi.geolocation.v1"))]
