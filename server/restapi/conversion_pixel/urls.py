from django.conf.urls import include
from django.conf.urls import url

import restapi.conversion_pixel.internal.urls
import restapi.conversion_pixel.v1.urls

urlpatterns = [
    url(r"^v1/accounts/", include(restapi.conversion_pixel.v1.urls, namespace="restapi.conversion_pixel.v1")),
    url(r"^internal/", include(restapi.conversion_pixel.internal.urls, namespace="restapi.conversion_pixel.internal")),
]
