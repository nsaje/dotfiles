from django.conf.urls import include
from django.conf.urls import url

import restapi.source.v1.urls

urlpatterns = [url(r"^v1/sources/", include(restapi.source.v1.urls, namespace="restapi.source.v1"))]
