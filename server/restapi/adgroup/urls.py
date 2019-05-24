from django.conf.urls import include
from django.conf.urls import url

import restapi.adgroup.internal.urls
import restapi.adgroup.v1.urls

urlpatterns = [
    url(r"^v1/adgroups/", include(restapi.adgroup.v1.urls, namespace="restapi.adgroup.v1")),
    url(r"^internal/adgroups/", include(restapi.adgroup.internal.urls, namespace="restapi.adgroup.internal")),
]
