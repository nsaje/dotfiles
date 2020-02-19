from django.conf.urls import include
from django.conf.urls import url

import restapi.publishers.v1.urls

urlpatterns = [url(r"^v1/adgroups/", include(restapi.publishers.v1.urls, namespace="restapi.publishers.v1"))]
