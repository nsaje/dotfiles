from django.conf.urls import include
from django.conf.urls import url

import restapi.bluekai.internal.urls
import restapi.bluekai.v1.urls

urlpatterns = [
    url(r"^v1/bluekai/", include(restapi.bluekai.v1.urls, namespace="restapi.bluekai.v1")),
    url(r"^internal/bluekai/", include(restapi.bluekai.internal.urls, namespace="restapi.bluekai.internal")),
]
