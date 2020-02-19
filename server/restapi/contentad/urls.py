from django.conf.urls import include
from django.conf.urls import url

import restapi.contentad.v1.urls

urlpatterns = [url(r"^v1/contentads/", include(restapi.contentad.v1.urls, namespace="restapi.contentad.v1"))]
